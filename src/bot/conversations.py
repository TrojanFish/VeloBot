import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
)

from src.config import ADMIN_ID
from src.locales import t
from src.database import get_user_lang, create_noise_ticket, set_ticket_admin_msg

logger = logging.getLogger(__name__)

ASK_PART, ASK_MEDIA, ASK_DESC = range(3)

PART_CHOICES = {
    "zh_hant": {
        "ask_part_cockpit": "🚲 龍頭 / 車把 / 碗組",
        "ask_part_drivetrain": "⚙️ 五通 / 曲柄 / 踏板",
        "ask_part_shifting": "🔄 前後變速與鏈條",
        "ask_part_brakes": "💿 碟煞卡鉗與輪組",
        "ask_part_seat": "🪑 座管與座墊區域",
        "ask_part_other": "❓ 其他疑難雜症"
    },
    "en": {
        "ask_part_cockpit": "🚲 Cockpit / Handlebar / Headset",
        "ask_part_drivetrain": "⚙️ BB / Crankset / Pedals",
        "ask_part_shifting": "🔄 Derailleurs & Chain",
        "ask_part_brakes": "💿 Disc Brakes & Wheels",
        "ask_part_seat": "🪑 Seatpost & Saddle Area",
        "ask_part_other": "❓ Other Symptoms"
    }
}

async def start_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """啟動異音門診投稿"""
    user = update.effective_user
    lang = get_user_lang(user.id, user.language_code)
    choices = PART_CHOICES.get(lang, PART_CHOICES["zh_hant"])

    keyboard = []
    keys = list(choices.keys())
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(choices[keys[i]], callback_data=keys[i])]
        if i + 1 < len(keys):
            row.append(InlineKeyboardButton(choices[keys[i+1]], callback_data=keys[i+1]))
        keyboard.append(row)

    text = t("ask_intro", lang=lang)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.effective_message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    return ASK_PART

async def select_part_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """處理部位選擇"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = get_user_lang(user.id, user.language_code)
    choices = PART_CHOICES.get(lang, PART_CHOICES["zh_hant"])

    part_label = choices.get(query.data, "Component")
    context.user_data["noise_part"] = part_label

    text = t("ask_step2", lang=lang, part=part_label)
    await query.edit_message_text(text, parse_mode="Markdown")
    return ASK_MEDIA

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """接收媒體"""
    msg = update.effective_message
    user = update.effective_user
    lang = get_user_lang(user.id, user.language_code)

    media_file_id = None
    media_type = "none"

    if msg.video:
        media_file_id = msg.video.file_id
        media_type = "video"
    elif msg.voice:
        media_file_id = msg.voice.file_id
        media_type = "voice"
    elif msg.audio:
        media_file_id = msg.audio.file_id
        media_type = "audio"
    elif msg.photo:
        media_file_id = msg.photo[-1].file_id
        media_type = "photo"

    context.user_data["noise_file_id"] = media_file_id
    context.user_data["noise_media_type"] = media_type

    await msg.reply_text(t("ask_step3", lang=lang), parse_mode="Markdown")
    return ASK_DESC

async def skip_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """跳過媒體上傳"""
    user = update.effective_user
    lang = get_user_lang(user.id, user.language_code)
    context.user_data["noise_file_id"] = None
    context.user_data["noise_media_type"] = "none"

    await update.effective_message.reply_text(t("ask_skipped", lang=lang), parse_mode="Markdown")
    return ASK_DESC

async def handle_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """接收描述並生成工單"""
    user = update.effective_user
    lang = get_user_lang(user.id, user.language_code)
    desc = update.effective_message.text
    part = context.user_data.get("noise_part", "未知部位")
    media_file_id = context.user_data.get("noise_file_id")
    media_type = context.user_data.get("noise_media_type", "none")

    ticket_id = create_noise_ticket(
        user_id=user.id,
        username=user.username or user.first_name,
        part=part,
        media_file_id=media_file_id,
        media_type=media_type,
        desc=desc
    )

    if ADMIN_ID:
        try:
            admin_caption = (
                f"🩺 **【車友異音門診新工單 #{ticket_id}】**\n\n"
                f"👤 **車友**：{user.first_name} (@{user.username or '無'})\n"
                f"🆔 **車友ID**：`{user.id}` (語言: `{lang}`)\n"
                f"🏷️ **故障部位**：{part}\n"
                f"📝 **實況描述**：{desc}\n\n"
                f"💡 **台長請直接【回覆/Reply】本消息**，輸入診斷分析，Bot 將自動推送給車友！"
            )

            sent_admin_msg = None
            if media_file_id:
                if media_type == "video":
                    sent_admin_msg = await context.bot.send_video(chat_id=ADMIN_ID, video=media_file_id, caption=admin_caption, parse_mode="Markdown")
                elif media_type in ("voice", "audio"):
                    sent_admin_msg = await context.bot.send_voice(chat_id=ADMIN_ID, voice=media_file_id, caption=admin_caption, parse_mode="Markdown")
                elif media_type == "photo":
                    sent_admin_msg = await context.bot.send_photo(chat_id=ADMIN_ID, photo=media_file_id, caption=admin_caption, parse_mode="Markdown")

            if not sent_admin_msg:
                sent_admin_msg = await context.bot.send_message(chat_id=ADMIN_ID, text=admin_caption, parse_mode="Markdown")

            if sent_admin_msg:
                set_ticket_admin_msg(ticket_id, sent_admin_msg.message_id)

        except Exception as e:
            logger.error(f"轉發異音工單失敗: {e}")

    await update.effective_message.reply_text(
        t("ask_submitted", lang=lang, ticket_id=ticket_id),
        parse_mode="Markdown"
    )

    context.user_data.clear()
    return ConversationHandler.END

async def cancel_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """取消投稿"""
    user = update.effective_user
    lang = get_user_lang(user.id, user.language_code)
    context.user_data.clear()
    await update.effective_message.reply_text(t("ask_canceled", lang=lang))
    return ConversationHandler.END

noise_conversation_handler = ConversationHandler(
    entry_points=[
        CommandHandler("ask", start_ask),
        CommandHandler("noise", start_ask),
        CallbackQueryHandler(start_ask, pattern="^entry_ask_noise$")
    ],
    states={
        ASK_PART: [
            CallbackQueryHandler(select_part_callback, pattern="^ask_part_")
        ],
        ASK_MEDIA: [
            MessageHandler(filters.VIDEO | filters.VOICE | filters.AUDIO | filters.PHOTO, handle_media),
            CommandHandler("skip", skip_media)
        ],
        ASK_DESC: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_desc)
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel_ask)
    ],
    allow_reentry=True,
    per_message=False
)
