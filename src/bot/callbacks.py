import sqlite3
import logging
from src.config import DB_FILE
from src.utils import _, get_user_lang
from src.bot.conversations import format_ride_card
from src.services.weather import get_weather_for_location
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def ride_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, ride_id_str = query.data.split('_', 2)[1:]
    ride_id, user = int(ride_id_str), query.from_user
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (telegram_user_id, strava_firstname) VALUES (?, ?)", (user.id, user.first_name))
    conn.commit()
    if action == "join":
        try:
            cursor.execute("INSERT INTO ride_participants (ride_id, telegram_user_id) VALUES (?, ?)", (ride_id, user.id))
            conn.commit()
        except sqlite3.IntegrityError: pass 
    elif action == "leave":
        cursor.execute("DELETE FROM ride_participants WHERE ride_id = ? AND telegram_user_id = ?", (ride_id, user.id))
        conn.commit()
    conn.close()
    new_card_text = await format_ride_card(ride_id, user.id)
    keyboard = [[
        InlineKeyboardButton(_(user.id, "ride_card_join"), callback_data=f"join_ride_{ride_id}"),
        InlineKeyboardButton(_(user.id, "ride_card_leave"), callback_data=f"leave_ride_{ride_id}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        if query.message and query.message.text != new_card_text:
            await query.edit_message_text(text=new_card_text, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        if "Message is not modified" not in str(e):
            logger.warning(f"更新约伴卡片失败: {e}")

async def location_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    location = context.user_data.get('location')
    if not location:
        await query.edit_message_text(text=_(user_id, "location_expired"))
        return
    if query.data == "loc_weather":
        await query.edit_message_text(text=_(user_id, "location_fetching_weather"))
        await get_weather_for_location(query.message.chat_id, location.latitude, location.longitude, context)
    elif query.data == "loc_route":
        await query.edit_message_text(text=_(user_id, "location_fetching_route"))
        # Import inside to avoid circular dependency if any
        from src.bot.handlers import get_routes_for_location
        await get_routes_for_location(query.message.chat_id, location.latitude, location.longitude, context)

async def language_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = query.data.split('set_lang_')[-1]
    user_id = query.from_user.id
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE telegram_user_id = ?", (lang_code, user_id))
    conn.commit()
    conn.close()
    
    names = {
        'en': 'English',
        'zh-hans': '简体中文',
        'zh-hant': '繁體中文',
        'es': 'Español',
        'de': 'Deutsch',
        'fr': 'Français',
        'it': 'Italiano'
    }
    lang_name = names.get(lang_code, lang_code)
    await query.edit_message_text(text=_(user_id, "language_set").format(lang=lang_name))
