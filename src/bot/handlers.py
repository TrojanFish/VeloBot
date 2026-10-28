import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.config import ADMIN_ID
from src.locales import t
from src.utils import get_specs, calculate_chain_length, get_pain_specs
from src.database import (
    get_user_lang, set_user_lang,
    get_video_by_id, get_video_by_admin_msg, update_video_kit,
    pop_kit_waiters, get_user_maintenance,
    get_ticket_by_admin_msg, update_ticket_status
)
from src.bot.conversations import start_ask

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 指令與 Deep Link 參數解析"""
    args = context.args
    user = update.effective_user
    lang = get_user_lang(user.id, user.language_code)

    # 1. 深度連結分發邏輯
    if args and len(args) > 0:
        param = args[0]
        logger.info(f"用戶 {user.id} 觸發 Deep Link: {param}")

        # 情況 A: 影片專屬物料清單 (?start=vid_xxxx)
        if param.startswith("vid_"):
            video_id = param.replace("vid_", "")
            video = get_video_by_id(video_id)

            if video and video.get("kit_content"):
                text = t(
                    "video_kit_title",
                    lang=lang,
                    title=video["title"],
                    content=video["kit_content"],
                    video_id=video_id
                )
                keyboard = [
                    [InlineKeyboardButton(t("btn_watch_yt", lang=lang), url=f"https://www.youtube.com/watch?v={video_id}")],
                    [InlineKeyboardButton(t("btn_ask", lang=lang), callback_data="entry_ask_noise")]
                ]
                await update.effective_message.reply_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    disable_web_page_preview=True
                )
                return
            else:
                title_display = video.get("title") if video else f"Video ({video_id})"
                text = t("video_kit_preparing", lang=lang, title=title_display)
                keyboard = [
                    [InlineKeyboardButton(t("btn_notify_waitlist", lang=lang), callback_data=f"waitlist_add_{video_id}")],
                    [InlineKeyboardButton(t("btn_watch_yt", lang=lang), url=f"https://www.youtube.com/watch?v={video_id}")]
                ]
                await update.effective_message.reply_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return

        # 情況 B: 異音門診直達 (?start=ask_noise)
        if param == "ask_noise":
            await start_ask(update, context)
            return

    # 2. 常規歡迎選單
    welcome_text = t("welcome", lang=lang, name=user.first_name)
    keyboard = [
        [
            InlineKeyboardButton(t("btn_torque", lang=lang), callback_data="torque_menu"),
            InlineKeyboardButton(t("btn_bb", lang=lang), callback_data="bb_menu")
        ],
        [
            InlineKeyboardButton(t("btn_pain", lang=lang), callback_data="pain_menu"),
            InlineKeyboardButton(t("btn_calc", lang=lang), callback_data="calc_menu")
        ],
        [
            InlineKeyboardButton(t("btn_mybike", lang=lang), callback_data="maint_view"),
            InlineKeyboardButton(t("btn_ask", lang=lang), callback_data="entry_ask_noise")
        ],
        [
            InlineKeyboardButton(t("btn_lang", lang=lang), callback_data="lang_select_menu")
        ]
    ]

    await update.effective_message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def pain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/pain 騎行疼痛自查與 Bike Fitting 處方籤指令"""
    user = update.effective_user
    lang = get_user_lang(user.id, user.language_code)
    pain_data = get_pain_specs(lang)
    areas = pain_data.get("areas", {})

    keyboard = []
    area_keys = list(areas.keys())
    for i in range(0, len(area_keys), 2):
        row = [InlineKeyboardButton(areas[area_keys[i]]["title"], callback_data=f"pain_area_{area_keys[i]}")]
        if i + 1 < len(area_keys):
            row.append(InlineKeyboardButton(areas[area_keys[i+1]]["title"], callback_data=f"pain_area_{area_keys[i+1]}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(t("btn_back_menu", lang=lang), callback_data="main_menu_refresh")])

    text = t("pain_intro", lang=lang)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.effective_message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/lang 語言切換指令"""
    user = update.effective_user
    lang = get_user_lang(user.id, user.language_code)
    prompt = t("lang_switch_prompt", lang=lang)
    keyboard = [
        [
            InlineKeyboardButton("🇹🇼 繁體中文", callback_data="lang_set_zh_hant"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_set_en")
        ]
    ]
    await update.effective_message.reply_text(prompt, reply_markup=InlineKeyboardMarkup(keyboard))

async def torque_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/torque 扭力速查指令"""
    user = update.effective_user
    lang = get_user_lang(user.id, user.language_code)
    specs = get_specs(lang).get("torque", {})

    keyboard = [
        [
            InlineKeyboardButton(specs.get("cockpit", {}).get("name", "🚲 龍頭/車把/座管"), callback_data="torque_cat_cockpit"),
            InlineKeyboardButton(specs.get("drivetrain", {}).get("name", "⚙️ 大盤/曲柄/踏板"), callback_data="torque_cat_drivetrain")
        ],
        [
            InlineKeyboardButton(specs.get("brakes_wheels", {}).get("name", "💿 碟煞/飛輪/輪組"), callback_data="torque_cat_brakes_wheels"),
            InlineKeyboardButton(specs.get("derailleurs", {}).get("name", "🔄 變速器/勾爪"), callback_data="torque_cat_derailleurs")
        ]
    ]
    await update.effective_message.reply_text(
        t("torque_title", lang=lang),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def bb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/bb 五通匹配器指令"""
    user = update.effective_user
    lang = get_user_lang(user.id, user.language_code)

    if lang == "en":
        frames = [
            ("BSA Threaded (68mm)", "bb_frame_BSA"),
            ("BB86 PressFit (41mm ID)", "bb_frame_BB86"),
            ("T47 Internal (85.5/86.5mm)", "bb_frame_T47_IN"),
            ("PF30 PressFit (46mm ID)", "bb_frame_PF30")
        ]
    else:
        frames = [
            ("BSA 英規螺紋 (68mm)", "bb_frame_BSA"),
            ("BB86 壓入式 (41mm內徑)", "bb_frame_BB86"),
            ("T47 內藏式 (85.5/86.5mm)", "bb_frame_T47_IN"),
            ("PF30 壓入式 (46mm內徑)", "bb_frame_PF30")
        ]

    keyboard = [[InlineKeyboardButton(name, callback_data=cb)] for name, cb in frames]
    await update.effective_message.reply_text(
        t("bb_title", lang=lang),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def calc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/calc 組裝計算器指令"""
    user = update.effective_user
    lang = get_user_lang(user.id, user.language_code)
    keyboard = [
        [InlineKeyboardButton(t("calc_btn_chain", lang=lang), callback_data="calc_chain")],
        [InlineKeyboardButton(t("calc_btn_tubeless", lang=lang), callback_data="calc_tubeless")]
    ]
    await update.effective_message.reply_text(
        t("calc_title", lang=lang),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def chain_calc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/chain 指令直接計算鏈條長度"""
    args = context.args
    user = update.effective_user
    lang = get_user_lang(user.id, user.language_code)

    if not args or len(args) < 3:
        await update.effective_message.reply_text(t("chain_usage", lang=lang), parse_mode="Markdown")
        return

    try:
        big_ring = int(args[0])
        max_cog = int(args[1])
        chainstay = float(args[2])

        recommended_links = calculate_chain_length(chainstay, big_ring, max_cog)

        text = t(
            "chain_result",
            lang=lang,
            big=big_ring,
            max_cog=max_cog,
            chainstay=chainstay,
            links=recommended_links
        )
        await update.effective_message.reply_text(text, parse_mode="Markdown")
    except ValueError:
        await update.effective_message.reply_text(t("chain_error", lang=lang))

async def mybike_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/mybike 個人保養管家"""
    user = update.effective_user
    lang = get_user_lang(user.id, user.language_code)
    presets = get_specs(lang).get("maintenance_presets", {})
    user_logs = {log["item_type"]: log for log in get_user_maintenance(user.id)}

    text = t("mybike_title", lang=lang)
    keyboard = []
    for k, v in presets.items():
        log = user_logs.get(k)
        if log:
            text += t("mybike_log_item", lang=lang, label=v["label"], last_date=log["last_done_date"], next_date=log["next_remind_date"])
        else:
            text += t("mybike_unrecorded", lang=lang, label=v["label"], cycle=v["cycle_days"])
        keyboard.append([InlineKeyboardButton(t("mybike_btn_done", lang=lang, label=v["label"]), callback_data=f"maint_done_{k}")])

    await update.effective_message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help 幫助指南"""
    user = update.effective_user
    lang = get_user_lang(user.id, user.language_code)
    if lang == "en":
        text = (
            "📖 **Road Bike Mechanic Toolkit Help**\n\n"
            "• /torque - Standard torque values for cockpit, BB, brakes, derailleurs\n"
            "• /bb - Frame shell and crank spindle compatibility wizard\n"
            "• /pain - Cycling pain self-check & Bike Fitting prescription\n"
            "• /calc - Chain length and tubeless sealant calculators\n"
            "• /chain - Fast chain link calculation (e.g. `/chain 50 34 410`)\n"
            "• /mybike - Periodic maintenance log & reminder (sealant, wax, brake fluid)\n"
            "• /ask - Noise clinic & troubleshooting submission\n"
            "• /lang - Switch language (繁體中文 / English)\n"
            "• /help - View this help guide\n"
        )
    else:
        text = (
            "📖 **公路車技師口袋工具箱指令表**\n\n"
            "• /torque - 關鍵部位標準鎖緊扭力速查（龍頭、車把、座管、中軸、碟煞、變速等）\n"
            "• /bb - 五通規格與大盤軸心相容匹配指南（墊圈配置與拆裝工具）\n"
            "• /pain - 騎行疼痛自查與 Bike Fitting 處方籤（膝蓋/腰背/手麻/坐墊等）\n"
            "• /calc - 組裝計算器選單\n"
            "• /chain - 快速計算鏈條標準節數（如 `/chain 50 34 410`）\n"
            "• /mybike - 個人週期保養到期提醒（無內胎補胎液、浸蠟、煞車油）\n"
            "• /ask - 異音與疑難雜症門診（提交影音讓台長親自診斷）\n"
            "• /lang - 切換機器人語言 (繁體中文 / English)\n"
            "• /help - 查看本使用指引\n"
        )
    await update.effective_message.reply_text(text, parse_mode="Markdown")

# ==================== 管理員長按 Reply 專屬工作流 ====================

async def admin_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    台長專屬免後台極速綁定：
    當管理員在手機端長按【回覆/Reply】機器人消息時觸發
    """
    user_id = update.effective_user.id
    if not ADMIN_ID or user_id != ADMIN_ID:
        return

    msg = update.effective_message
    if not msg.reply_to_message:
        return

    replied_msg_id = msg.reply_to_message.message_id
    admin_reply_text = msg.text

    # 1. 回覆新影片錄入通知
    video = get_video_by_admin_msg(replied_msg_id)
    if video:
        video_id = video["video_id"]
        update_video_kit(video_id, admin_reply_text)
        logger.info(f"管理員為影片 {video_id} 錄入物料清單。")

        waiters = pop_kit_waiters(video_id)
        dispatched_count = 0
        for waiter_id in waiters:
            try:
                waiter_lang = get_user_lang(waiter_id)
                await context.bot.send_message(
                    chat_id=waiter_id,
                    text=t("waitlist_broadcast", lang=waiter_lang, title=video["title"], content=admin_reply_text, video_id=video_id),
                    parse_mode="Markdown"
                )
                dispatched_count += 1
            except Exception as e:
                logger.error(f"向預約車友 {waiter_id} 補發物料失敗: {e}")

        await msg.reply_text(
            f"🎉 **已成功綁定《{video['title']}》的專屬組裝物料！**\n\n"
            f"📢 已自動補發給 {dispatched_count} 位預約等待的車友。"
        )
        return

    # 2. 回覆異音門診工單
    ticket = get_ticket_by_admin_msg(replied_msg_id)
    if ticket:
        ticket_id = ticket["ticket_id"]
        target_user_id = ticket["user_id"]
        target_lang = get_user_lang(target_user_id)

        if target_lang == "en":
            diag_text = (
                f"🩺 **[Host Feedback on your Noise Ticket #{ticket_id}]**\n\n"
                f"🏷️ **Component**: {ticket['part_category']}\n"
                f"📝 **Description**: {ticket['description']}\n\n"
                f"👨‍🔧 **Diagnostic Advice**:\n{admin_reply_text}\n\n"
                f"Hope this helps with your bike tuning!"
            )
        else:
            diag_text = (
                f"🩺 **【台長對你的異音工單 #{ticket_id} 進行了診斷回覆】**\n\n"
                f"🏷️ **涉及部位**：{ticket['part_category']}\n"
                f"📝 **你的描述**：{ticket['description']}\n\n"
                f"👨‍🔧 **台長診斷與建議**：\n{admin_reply_text}\n\n"
                f"希望對你的調車有所幫助！"
            )

        try:
            await context.bot.send_message(chat_id=target_user_id, text=diag_text, parse_mode="Markdown")
            update_ticket_status(ticket_id, "replied")
            await msg.reply_text(f"✅ 已成功將診斷答覆推送給車友 (ID: {target_user_id})！工單已標記為完成。")
        except Exception as e:
            await msg.reply_text(f"❌ 推送失敗，車友可能已封鎖機器人: {e}")
        return
