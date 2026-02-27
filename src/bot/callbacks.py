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

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    await query.answer()

    if data == "menu_main":
        from src.bot.handlers import menu_command
        await menu_command(update, context)
        return

    keyboard = []
    text = ""

    if data == "menu_activity":
        text = f"🚴 **{_(user_id, 'menu_activity')}**"
        keyboard = [
            [InlineKeyboardButton(_(user_id, "get_last_activity"), callback_data="cmd_last_act")],
            [InlineKeyboardButton(_(user_id, "my_rides"), callback_data="cmd_my_rides")],
            [InlineKeyboardButton(_(user_id, "back_to_menu"), callback_data="menu_main")]
        ]
    elif data == "menu_stats":
        text = f"🏆 **{_(user_id, 'menu_stats')}**"
        keyboard = [
            [InlineKeyboardButton(_(user_id, "report"), callback_data="cmd_report")],
            [InlineKeyboardButton(_(user_id, "leaderboard"), callback_data="cmd_leaderboard")],
            [InlineKeyboardButton(_(user_id, "back_to_menu"), callback_data="menu_main")]
        ]
    elif data == "menu_gear":
        text = f"🔧 **{_(user_id, 'menu_gear')}**"
        keyboard = [
            [InlineKeyboardButton(_(user_id, "maintenance"), callback_data="cmd_maintenance")],
            [InlineKeyboardButton(_(user_id, "back_to_menu"), callback_data="menu_main")]
        ]
    elif data == "menu_awards":
        text = f"🏅 **{_(user_id, 'menu_awards')}**"
        keyboard = [
            [InlineKeyboardButton(_(user_id, "my_achievements"), callback_data="cmd_achievements")],
            [InlineKeyboardButton(_(user_id, "back_to_menu"), callback_data="menu_main")]
        ]
    elif data == "menu_tools":
        text = f"🌍 **{_(user_id, 'menu_tools')}**"
        keyboard = [
            [InlineKeyboardButton(_(user_id, "weather"), callback_data="cmd_weather")],
            [InlineKeyboardButton(_(user_id, "route"), callback_data="cmd_route")],
            [InlineKeyboardButton(_(user_id, "back_to_menu"), callback_data="menu_main")]
        ]
    elif data == "menu_settings":
        text = f"⚙️ **{_(user_id, 'menu_settings')}**"
        keyboard = [
            [InlineKeyboardButton(_(user_id, "language"), callback_data="cmd_lang")],
            [InlineKeyboardButton(_(user_id, "units"), callback_data="cmd_units")],
            [InlineKeyboardButton(_(user_id, "toggle_strava_privacy"), callback_data="cmd_privacy")],
            [InlineKeyboardButton(_(user_id, "back_to_menu"), callback_data="menu_main")]
        ]
    elif data.startswith("cmd_"):
        # 处理菜单中的快捷指令触发
        cmd = data.replace("cmd_", "")
        from src.bot.handlers import (
            get_last_activity, my_rides, get_report, get_leaderboard,
            maintenance_command, my_achievements, weather, route,
            language_command, units_command, toggle_strava_privacy
        )
        cmd_map = {
            "last_act": get_last_activity, "my_rides": my_rides,
            "report": get_report, "leaderboard": get_leaderboard,
            "maintenance": maintenance_command, "achievements": my_achievements,
            "weather": weather, "route": route, "lang": language_command,
            "units": units_command, "privacy": toggle_strava_privacy
        }
        handler = cmd_map.get(cmd)
        if handler:
            # 修改 context 避免某些 handler 检查 message.text
            await handler(update, context)
        return

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
