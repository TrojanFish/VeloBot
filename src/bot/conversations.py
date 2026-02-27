import sqlite3
import logging
from datetime import datetime
from src.config import DB_FILE, TELEGRAM_CHAT_ID
from src.utils import _, get_user_lang
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

logger = logging.getLogger(__name__)

RIDE_TITLE, RIDE_TIME, RIDE_ROUTE, RIDE_DESC = range(4)

async def create_ride(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(_(user.id, "create_ride_start"))
    return RIDE_TITLE

async def ride_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data['ride_title'] = update.message.text
    await update.message.reply_text(_(user_id, "create_ride_title_ok"))
    return RIDE_TIME

async def ride_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        dt_obj = datetime.strptime(update.message.text, '%Y-%m-%d %H:%M')
        context.user_data['ride_time'] = dt_obj
        await update.message.reply_text(_(user_id, "create_ride_time_ok"))
        return RIDE_ROUTE
    except ValueError:
        await update.message.reply_text(_(user_id, "create_ride_time_error"))
        return RIDE_TIME

async def ride_route(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data['ride_route'] = update.message.text
    await update.message.reply_text(_(user_id, "create_ride_route_ok"))
    return RIDE_DESC

async def ride_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data['ride_desc'] = update.message.text if update.message.text.lower() not in ['无', 'no', 'none'] else "无"
    ride, creator = context.user_data, update.effective_user
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO rides (creator_user_id, group_chat_id, title, ride_time, route, description) VALUES (?, ?, ?, ?, ?, ?)",
                   (creator.id, update.message.chat_id, ride['ride_title'], ride['ride_time'].timestamp(), ride['ride_route'], ride['ride_desc']))
    ride_id = cursor.lastrowid
    cursor.execute("INSERT INTO ride_participants (ride_id, telegram_user_id) VALUES (?, ?)", (ride_id, creator.id))
    conn.commit()
    conn.close()
    
    ride_card_text = await format_ride_card(ride_id, user_id)
    keyboard = [[
        InlineKeyboardButton(_(user_id, "ride_card_join"), callback_data=f"join_ride_{ride_id}"),
        InlineKeyboardButton(_(user_id, "ride_card_leave"), callback_data=f"leave_ride_{ride_id}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    sent_message = await context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=ride_card_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE rides SET message_id = ? WHERE ride_id = ?", (sent_message.message_id, ride_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(_(user_id, "create_ride_desc_ok"))
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(_(user_id, "create_ride_cancel"))
    context.user_data.clear()
    return ConversationHandler.END

async def format_ride_card(ride_id, lang_user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT r.title, r.ride_time, r.route, r.description, u.strava_firstname FROM rides r JOIN users u ON r.creator_user_id = u.telegram_user_id WHERE r.ride_id = ?", (ride_id,))
    ride_info = cursor.fetchone()
    cursor.execute("SELECT u.strava_firstname FROM ride_participants rp JOIN users u ON rp.telegram_user_id = u.telegram_user_id WHERE rp.ride_id = ?", (ride_id,))
    participants = cursor.fetchall()
    conn.close()
    if not ride_info: return _(lang_user_id, "ride_card_invalid")
    title, ride_time_ts, route, desc, creator_name = ride_info
    ride_time_str = datetime.fromtimestamp(ride_time_ts).strftime('%Y-%m-%d %H:%M')
    participant_names = [p[0] for p in participants if p[0]]
    
    card = [
        f"🚴 **{title}** 🚴‍♀️",
        "--------------------",
        _(lang_user_id, "ride_card_time").format(time=ride_time_str),
        _(lang_user_id, "ride_card_route").format(route=route),
        _(lang_user_id, "ride_card_desc").format(desc=desc),
        _(lang_user_id, "ride_card_creator").format(name=creator_name),
        _(lang_user_id, "ride_card_participants").format(
            count=len(participant_names),
            names=', '.join(participant_names) if participant_names else _(lang_user_id, "ride_card_no_participants")
        )
    ]
    return "\n".join(card)
