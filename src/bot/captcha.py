import time
import logging
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.config import GROUP_ID, CHANNEL_ID, ADMIN_ID, ENABLE_CAPTCHA
from src.locales import t
from src.database import (
    get_user_lang, get_system_setting,
    load_valid_subscribers, save_subscriber_cache, evict_subscriber_cache
)

logger = logging.getLogger(__name__)

# 緩存已驗證關注的成員（避免每個發言都頻繁調用 API 觸發頻控 429）
# 啟動時自 SQLite 自動恢復有效快取，徹底杜絕重啟後的 429 請求風暴
VERIFIED_SUBSCRIBERS: dict[int, float] = load_valid_subscribers()
_channel_url_cache = None

# ==================== 快取清理與持久化工具 ====================

def _cache_subscriber(user_id: int, expire_time: float):
    """將已驗證成員寫入記憶體快取並同步持久化到 SQLite"""
    VERIFIED_SUBSCRIBERS[user_id] = expire_time
    save_subscriber_cache(user_id, expire_time)

def _evict_expired_cache():
    """清除 VERIFIED_SUBSCRIBERS 中所有已過期的條目，防止記憶體無限膨脹"""
    now = time.time()
    expired = [uid for uid, exp in VERIFIED_SUBSCRIBERS.items() if exp <= now]
    for uid in expired:
        del VERIFIED_SUBSCRIBERS[uid]
        evict_subscriber_cache(uid)

def is_forcesub_enabled() -> bool:
    """檢查強制關注頻道功能是否開啟（預設開啟）"""
    db_val = get_system_setting("forcesub_enabled")
    if db_val is not None:
        return db_val.lower() in ("true", "1", "yes", "on")
    db_captcha = get_system_setting("captcha_enabled")
    if db_captcha is not None:
        return db_captcha.lower() in ("true", "1", "yes", "on")
    return ENABLE_CAPTCHA

async def get_channel_url(bot) -> str:
    """動態獲取或解析頻道的直達鏈接（自帶緩存）"""
    global _channel_url_cache
    if _channel_url_cache:
        return _channel_url_cache

    if not CHANNEL_ID:
        return "https://t.me"

    try:
        chat = await bot.get_chat(CHANNEL_ID)
        if chat.username:
            _channel_url_cache = f"https://t.me/{chat.username}"
        elif chat.invite_link:
            _channel_url_cache = chat.invite_link
        else:
            _channel_url_cache = await bot.export_chat_invite_link(CHANNEL_ID)
        return _channel_url_cache
    except Exception as e:
        logger.warning(f"獲取頻道鏈接失敗: {e}")
        if str(CHANNEL_ID).startswith("@"):
            return f"https://t.me/{str(CHANNEL_ID)[1:]}"
        return "https://t.me"

async def is_user_subscribed(bot, user_id: int) -> bool:
    """調用 Telegram 官方 API 檢驗用戶是否已關注指定頻道"""
    if not CHANNEL_ID:
        return True

    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # 只要在頻道中且不是 left 或 kicked 就算已關注
        return member.status in ("creator", "administrator", "member", "restricted")
    except Exception as e:
        logger.warning(f"檢驗用戶 {user_id} 頻道關注狀態時異常 (可能 Bot 未加入頻道或未給管理員權限): {e}")
        # 故障保護：若 Bot 自身無權限查詢，避免誤鎖所有正常發言
        return True

# ==================== 模式 A：純關注頻道驗證與攔截 ====================

async def new_member_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """新成員入群事件處理：未關注頻道者立刻禁言並彈出引流關注卡片（10 分鐘後自動銷毀）"""
    if not is_forcesub_enabled():
        return

    message = update.message
    if not message or not message.new_chat_members:
        return

    chat_id = update.effective_chat.id
    if GROUP_ID and str(chat_id) != str(GROUP_ID):
        return

    # 機會性清理過期快取條目（每次新成員進群時觸發，低開銷）
    _evict_expired_cache()

    for new_user in message.new_chat_members:
        if new_user.is_bot:
            continue

        user_id = new_user.id
        user_name = new_user.first_name or "Rider"
        lang = get_user_lang(user_id, new_user.language_code)

        # 1. 檢查是否已經關注了頻道
        is_subbed = await is_user_subscribed(context.bot, user_id)
        if is_subbed:
            _cache_subscriber(user_id, time.time() + 3600)
            logger.info(f"新成員 {user_name} ({user_id}) 入群時已關注頻道，免除禁言！")
            continue

        # 2. 未關注：先禁言
        try:
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False)
            )
            logger.info(f"新成員 {user_name} ({user_id}) 未關注頻道，已實施入群禁言。")
        except Exception as e:
            logger.error(f"限制用戶 {user_id} 權限失敗: {e}")

        # 3. 發送引流關注卡片
        channel_url = await get_channel_url(context.bot)
        keyboard = [
            [InlineKeyboardButton(t("forcesub_btn_channel", lang), url=channel_url)],
            [InlineKeyboardButton(t("forcesub_btn_verify", lang), callback_data=f"fsb:{user_id}:{lang}")]
        ]

        prompt_text = t(
            "forcesub_prompt",
            lang=lang,
            name=user_name,
            user_id=user_id
        )

        try:
            sent = await context.bot.send_message(
                chat_id=chat_id,
                text=prompt_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
            # 10 分鐘後自動清理引流卡片，防止卡片長期積壓刷屏
            if context.job_queue:
                _chat_id = sent.chat_id
                _msg_id = sent.message_id

                async def _delete_join_card(ctx):
                    try:
                        await ctx.bot.delete_message(chat_id=_chat_id, message_id=_msg_id)
                    except Exception:
                        pass

                context.job_queue.run_once(_delete_join_card, when=600)
        except Exception as e:
            logger.error(f"發送關注引流消息失敗: {e}")

async def group_message_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """群內常規消息監聽攔截：未關注頻道者發送的任何消息秒刪並提示關注"""
    if not is_forcesub_enabled():
        return

    message = update.effective_message
    # 修復 Bug 1：原先只攔截 message.text，圖片/貼圖/語音可繞過。現在只要有消息即核驗。
    if not message:
        return

    chat = update.effective_chat
    if not chat or chat.type not in ("group", "supergroup"):
        return

    if GROUP_ID and str(chat.id) != str(GROUP_ID):
        return

    user = update.effective_user
    if not user or user.is_bot:
        return

    # 管理員和台長直接放行
    if ADMIN_ID and user.id == ADMIN_ID:
        return

    # 檢查本地緩存（命中緩存則 0 API 開銷秒放行）
    now = time.time()
    if user.id in VERIFIED_SUBSCRIBERS and VERIFIED_SUBSCRIBERS[user.id] > now:
        return

    # 檢查是否為群管理員（管理員豁免）
    try:
        member = await chat.get_member(user.id)
        if member.status in ("creator", "administrator"):
            _cache_subscriber(user.id, now + 86400)
            return
    except Exception:
        pass

    # 查驗頻道關注狀態
    is_subbed = await is_user_subscribed(context.bot, user.id)
    if is_subbed:
        _cache_subscriber(user.id, now + 3600)
        return

    # 尚未關注頻道：秒刪發言 + 禁言 + 彈出提示卡片
    try:
        await message.delete()
    except Exception:
        pass

    try:
        await context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
    except Exception:
        pass

    channel_url = await get_channel_url(context.bot)
    lang = get_user_lang(user.id, user.language_code)
    keyboard = [
        [InlineKeyboardButton(t("forcesub_btn_channel", lang), url=channel_url)],
        [InlineKeyboardButton(t("forcesub_btn_verify", lang), callback_data=f"fsb:{user.id}:{lang}")]
    ]

    try:
        warn_msg = await chat.send_message(
            text=t("forcesub_speak_warn", lang, name=user.first_name or "Rider", user_id=user.id),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
        # 修復 Bug 2：lambda 無法 await 異步方法，改為標準 async job 函數
        # 15 秒後自動清理提示消息，保持群內整潔
        if context.job_queue:
            _chat_id = warn_msg.chat_id
            _msg_id = warn_msg.message_id

            async def _delete_warn_card(ctx):
                try:
                    await ctx.bot.delete_message(chat_id=_chat_id, message_id=_msg_id)
                except Exception:
                    pass

            context.job_queue.run_once(_delete_warn_card, when=15)
    except Exception as e:
        logger.warning(f"發送發言攔截卡片失敗: {e}")

async def handle_forcesub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理車友點擊【✅ 我已關注，解除禁言】核驗按鈕"""
    query = update.callback_query
    data = query.data  # fsb:{user_id}:{lang}
    parts = data.split(":")
    if len(parts) < 3:
        return

    target_user_id = int(parts[1])
    lang = parts[2] if len(parts) > 2 else "zh_hant"

    # 防代點
    if query.from_user.id != target_user_id:
        await query.answer(t("forcesub_not_you", lang=lang), show_alert=True)
        return

    # 再次核實頻道關注
    is_subbed = await is_user_subscribed(context.bot, target_user_id)
    chat_id = update.effective_chat.id

    if is_subbed:
        try:
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=target_user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
            )
            _cache_subscriber(target_user_id, time.time() + 3600)
            await query.answer(t("forcesub_success", lang=lang), show_alert=False)
            pass_text = f"✅ [{query.from_user.first_name}](tg://user?id={target_user_id}) " + t("forcesub_success", lang=lang)
            await query.edit_message_text(pass_text, parse_mode="Markdown")

            # 修復 Bug 2：lambda 無法 await 異步方法，改為標準 async job 函數
            # 5 秒後銷毀通過提示
            if context.job_queue:
                _chat_id = chat_id
                _msg_id = query.message.message_id

                async def _delete_pass_card(ctx):
                    try:
                        await ctx.bot.delete_message(chat_id=_chat_id, message_id=_msg_id)
                    except Exception:
                        pass

                context.job_queue.run_once(_delete_pass_card, when=5)
        except Exception as e:
            logger.error(f"解禁用戶 {target_user_id} 失敗: {e}")
    else:
        # 尚未檢測到關注
        await query.answer(t("forcesub_not_yet", lang=lang), show_alert=True)
