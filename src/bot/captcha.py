import random
import logging
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.config import GROUP_ID
from src.locales import t
from src.utils import get_specs
from src.database import get_user_lang

logger = logging.getLogger(__name__)

PENDING_VERIFICATIONS = {}

async def new_member_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """新成員入群觸發硬核常識問答驗證（支援繁中與英文）"""
    message = update.message
    if not message or not message.new_chat_members:
        return

    chat_id = update.effective_chat.id
    if GROUP_ID and str(chat_id) != str(GROUP_ID):
        return

    for new_user in message.new_chat_members:
        if new_user.is_bot:
            continue

        user_id = new_user.id
        user_name = new_user.first_name or "Rider"
        lang = get_user_lang(user_id, new_user.language_code)

        # 1. 禁言
        try:
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False)
            )
        except Exception as e:
            logger.error(f"限制用戶 {user_id} 權限失敗: {e}")

        # 2. 獲取題目
        specs = get_specs(lang)
        questions = specs.get("captcha_questions", [])
        if not questions:
            continue

        q_idx = random.randint(0, len(questions) - 1)
        q_data = questions[q_idx]

        # 3. 構造 3 選 1 按鈕
        keyboard = []
        for opt_idx, opt_text in enumerate(q_data["options"]):
            cb_data = f"cpt:{user_id}:{q_idx}:{opt_idx}:{lang}"
            keyboard.append([InlineKeyboardButton(opt_text, callback_data=cb_data)])

        prompt_text = t(
            "captcha_prompt",
            lang=lang,
            name=user_name,
            user_id=user_id,
            question=q_data["q"]
        )

        try:
            sent_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=prompt_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            job_name = f"captcha_timeout_{chat_id}_{user_id}"
            if context.job_queue:
                context.job_queue.run_once(
                    captcha_timeout_callback,
                    when=120,
                    data={"chat_id": chat_id, "user_id": user_id, "message_id": sent_msg.message_id},
                    name=job_name
                )

            PENDING_VERIFICATIONS[user_id] = {
                "chat_id": chat_id,
                "message_id": sent_msg.message_id,
                "job_name": job_name
            }
        except Exception as e:
            logger.error(f"發送入群驗證消息失敗: {e}")

async def captcha_timeout_callback(context: ContextTypes.DEFAULT_TYPE):
    """超時未作答踢出"""
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    user_id = job_data["user_id"]
    msg_id = job_data["message_id"]

    PENDING_VERIFICATIONS.pop(user_id, None)

    try:
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
        logger.info(f"用戶 {user_id} 驗證超時已被移出群組 {chat_id}")
    except Exception as e:
        logger.error(f"超時移出用戶 {user_id} 失敗: {e}")

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except Exception:
        pass

async def handle_captcha_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理答題點選"""
    query = update.callback_query
    data = query.data # cpt:{user_id}:{q_idx}:{opt_idx}:{lang}
    parts = data.split(":")
    if len(parts) < 4:
        return

    target_user_id = int(parts[1])
    q_idx = int(parts[2])
    chosen_opt_idx = int(parts[3])
    lang = parts[4] if len(parts) > 4 else "zh_hant"

    if query.from_user.id != target_user_id:
        await query.answer(t("captcha_not_you", lang=lang), show_alert=True)
        return

    specs = get_specs(lang)
    questions = specs.get("captcha_questions", [])
    if q_idx >= len(questions):
        await query.answer("Expired / 驗證已過期", show_alert=True)
        return

    correct_idx = questions[q_idx].get("answer_index", 0)
    chat_id = update.effective_chat.id

    info = PENDING_VERIFICATIONS.pop(target_user_id, None)
    if info and context.job_queue:
        current_jobs = context.job_queue.get_jobs_by_name(info["job_name"])
        for job in current_jobs:
            job.schedule_removal()

    if chosen_opt_idx == correct_idx:
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
            await query.answer(t("captcha_correct", lang=lang), show_alert=False)
            pass_text = t("captcha_passed_msg", lang=lang, name=query.from_user.first_name, user_id=target_user_id)
            await query.edit_message_text(pass_text, parse_mode="Markdown")

            if context.job_queue:
                context.job_queue.run_once(
                    lambda ctx: ctx.bot.delete_message(chat_id=chat_id, message_id=query.message.message_id),
                    when=5
                )
        except Exception as e:
            logger.error(f"解禁用戶 {target_user_id} 失敗: {e}")
    else:
        await query.answer(t("captcha_wrong", lang=lang), show_alert=True)
        try:
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=target_user_id)
            await context.bot.unban_chat_member(chat_id=chat_id, user_id=target_user_id)
            await query.message.delete()
        except Exception as e:
            logger.error(f"踢出答錯用戶 {target_user_id} 失敗: {e}")
