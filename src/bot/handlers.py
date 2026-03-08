import sqlite3
import os
import json
import logging
import asyncio
import feedparser
import httpx
from datetime import datetime, timezone, timedelta
from src.config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, BOT_SERVER_URL, YOUTUBE_CHANNEL_RSS_URL
from src.database import get_db_connection
from src.utils import _, format_duration
from src.services.strava import format_activity_details
from src.services.weather import get_weather_for_city, get_weather_for_location
from src.services.visuals import generate_suffer_trend
from stravalib.client import Client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes
from src.services.ai_coach import ask_ai_coach, transcribe_voice
import re

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.effective_message.reply_text(_(user_id, "start_welcome"))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.effective_message.reply_text(_(user_id, "help_text"))

async def link_strava(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    client = Client()
    redirect_uri = f"{BOT_SERVER_URL}/strava_auth"
    authorize_url = client.authorization_url(client_id=STRAVA_CLIENT_ID, redirect_uri=redirect_uri, scope=['read', 'activity:read_all'], state=str(user_id))
    keyboard = [[InlineKeyboardButton(_(user_id, "link_strava_button"), url=authorize_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(_(user_id, "link_strava_prompt"), reply_markup=reply_markup)

async def toggle_strava_privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT strava_notification_mode FROM users WHERE telegram_user_id = ?", (user_id,))
    result = cursor.fetchone()
    if not result:
        await update.effective_message.reply_text(_(user_id, "privacy_not_linked"))
    else:
        current_mode = result[0]
        new_mode = 'private' if current_mode == 'public' else 'public'
        cursor.execute("UPDATE users SET strava_notification_mode = ? WHERE telegram_user_id = ?", (new_mode, user_id))
        conn.commit()
        if new_mode == 'public':
            await update.effective_message.reply_text(_(user_id, "privacy_switched_public"))
        else:
            await update.effective_message.reply_text(_(user_id, "privacy_switched_private"))
    conn.close()

async def get_last_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT strava_access_token, strava_refresh_token, strava_token_expires_at FROM users WHERE telegram_user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    if not user_data or not user_data[0]:
        await update.effective_message.reply_text(_(user_id, "privacy_not_linked"))
        conn.close()
        return
    access_token, refresh_token, expires_at = user_data
    client = Client()
    try:
        if datetime.now(timezone.utc).timestamp() > expires_at:
            response = client.refresh_access_token(client_id=STRAVA_CLIENT_ID, client_secret=STRAVA_CLIENT_SECRET, refresh_token=refresh_token)
            access_token, refresh_token, expires_at = response['access_token'], response['refresh_token'], response['expires_at']
            cursor.execute('UPDATE users SET strava_access_token=?, strava_refresh_token=?, strava_token_expires_at=? WHERE telegram_user_id=?', (access_token, refresh_token, expires_at, user_id))
            conn.commit()
        client.access_token = access_token
        activities = list(client.get_activities(limit=1))
        if not activities:
            await context.bot.send_message(chat_id=user_id, text=_(user_id, "last_activity_not_found"))
        else:
            activity = activities[0]
            activity_type_emoji = {"Ride": "🚴", "Run": "🏃", "Swim": "🏊", "Walk": "🚶", "Hike": "⛰️", "AlpineSki": "⛷️", "Workout": "💪", "Yoga": "🧘", "VirtualRide": "💻🚴"}.get(str(activity.type), "🏆")
            message_lines = [_(user_id, "your_last_activity_is"), f"{activity_type_emoji} **{activity.name}**"]
            message_lines.extend(format_activity_details(activity, user_id))
            message_lines.append(f"\n🔗 [{_(user_id, 'activity_view_on_strava')}](https://www.strava.com/activities/{activity.id})")
            await context.bot.send_message(chat_id=user_id, text="\n".join(message_lines), parse_mode='Markdown')
        if update.effective_message.chat.type != 'private':
            await update.effective_message.reply_text(_(user_id, "last_activity_sent_privately"))
    except Exception as e:
        logger.error(f"为用户 {user_id} 获取最新活动时出错: {e}")
        await update.effective_message.reply_text(_(user_id, "last_activity_error"))
    finally:
        conn.close()

async def get_last_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    placeholder_message = None
    try:
        placeholder_message = await update.effective_message.reply_text(_(user_id, "fetching_video"))
        feed = await asyncio.to_thread(feedparser.parse, YOUTUBE_CHANNEL_RSS_URL)
        if feed.entries:
            latest_video = feed.entries[0]
            message = _(user_id, "new_video_notification").format(author=latest_video.author, title=latest_video.title) + f"\n\n{latest_video.link}"
            await placeholder_message.edit_text(message, parse_mode='Markdown', disable_web_page_preview=False)
        else:
            await placeholder_message.edit_text(_(user_id, "video_not_found"))
    except Exception as e:
        logger.error(f"手动获取 YouTube 视频时发生错误: {e}")
        error_message = _(user_id, "video_error")
        if placeholder_message: await placeholder_message.edit_text(error_message)
        else: await update.effective_message.reply_text(error_message)

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.effective_message.new_chat_members:
        if member.is_bot: continue
        user_mention = member.mention_html()
        welcome_message = _(member.id, "welcome_new_member").format(mention=user_mention)
        await update.effective_message.reply_text(welcome_message, parse_mode='HTML')

async def get_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    from src.bot.tasks import generate_and_send_user_report
    await generate_and_send_user_report(user_id, context.bot, 'demand')

async def get_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    period_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    conn = get_db_connection()
    cursor = conn.cursor()
    def query_leaderboard(order_by_column):
        cursor.execute(f"SELECT u.strava_firstname, SUM(a.{order_by_column}) as total FROM activities a JOIN users u ON a.telegram_user_id = u.telegram_user_id WHERE a.start_date >= ? GROUP BY u.telegram_user_id ORDER BY total DESC LIMIT 10", (period_start.timestamp(),))
        return cursor.fetchall()
    dist_leaders, time_leaders, elev_leaders = query_leaderboard('distance'), query_leaderboard('moving_time'), query_leaderboard('elevation_gain')
    conn.close()
    def format_leaders(title_key, leaders, unit):
        lines = [f"*{_(user_id, title_key)}*"]
        for i, (name, total) in enumerate(leaders):
            name = name or _(user_id, "leaderboard_anonymous_user")
            value = f"{total:.2f}" if unit == "km" else format_duration(total) if unit == "time" else f"{total:.0f}"
            lines.append(f"{'🥇🥈🥉'[i] if i < 3 else '🔹'} {name}: {value} {unit if unit != 'time' else ''}")
        return "\n".join(lines)
    if not dist_leaders:
        await update.effective_message.reply_text(_(user_id, "leaderboard_no_activity"))
        return
    message = [
        _(user_id, "leaderboard_title"),
        format_leaders("leaderboard_dist_king", dist_leaders, "km"),
        "\n" + format_leaders("leaderboard_climb_king", elev_leaders, "m"),
        "\n" + format_leaders("leaderboard_time_king", time_leaders, "time")
    ]
    await update.effective_message.reply_text("\n".join(message), parse_mode='Markdown')

async def my_rides(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now_ts = datetime.now(timezone.utc).timestamp()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.title, r.ride_time, r.creator_user_id
        FROM rides r JOIN ride_participants rp ON r.ride_id = rp.ride_id
        WHERE rp.telegram_user_id = ? AND r.ride_time > ? AND r.status = 'active'
        ORDER BY r.ride_time ASC
    """, (user_id, now_ts))
    rides = cursor.fetchall()
    conn.close()
    if not rides:
        await context.bot.send_message(chat_id=user_id, text=_(user_id, "my_rides_no_activity"))
        if update.effective_message.chat.type != 'private': await update.effective_message.reply_text(_(user_id, "my_rides_sent_privately"))
        return
    message_lines = [_(user_id, "my_rides_title")]
    for title, ride_time_ts, creator_id in rides:
        ride_time_str = datetime.fromtimestamp(ride_time_ts).strftime('%Y-%m-%d %H:%M')
        role = _(user_id, "my_rides_creator") if creator_id == user_id else ""
        message_lines.append(f"- *{title}*{role}\n  `{ride_time_str}`")
    await context.bot.send_message(chat_id=user_id, text="\n".join(message_lines), parse_mode='Markdown')
    if update.message.chat.type != 'private': await update.message.reply_text(_(user_id, "my_rides_sent_privately"))

async def my_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    from src.locales import LOCALIZED_ACHIEVEMENTS
    from src.utils import get_achievement_text
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT achievement_id FROM achievements WHERE telegram_user_id = ?", (user_id,))
    unlocked_ids = {row[0] for row in cursor.fetchall()}
    conn.close()
    if not unlocked_ids:
        await update.effective_message.reply_text(_(user_id, "my_achievements_no_activity"))
        return
    message_lines = [_(user_id, "my_achievements_title")]
    for ach_id, _unused in LOCALIZED_ACHIEVEMENTS['en'].items():
        ach_data = get_achievement_text(user_id, ach_id)
        if ach_id in unlocked_ids: message_lines.append(f"✅ *{ach_data['name']}*: _{ach_data['desc']}_")
        else: message_lines.append(f"❌ *{ach_data['name']}*: _{ach_data['desc']}_")
    await update.message.reply_text("\n".join(message_lines), parse_mode='Markdown')

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args: await update.effective_message.reply_text(_(user_id, "weather_prompt"))
    else: await get_weather_for_city(update.message.chat_id, " ".join(context.args), context, user_id)

async def route(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.effective_message.reply_text(_(user_id, "route_prompt"))
        return
    location_name = " ".join(context.args)
    async with httpx.AsyncClient() as client:
        try:
            params = {"name": location_name, "count": 1, "language": "zh", "format": "json"}
            geo_url = "https://geocoding-api.open-meteo.com/v1/search"
            geo_resp = await client.get(geo_url, params=params)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            if not geo_data.get("results"):
                await update.effective_message.reply_text(_(user_id, "route_location_not_found").format(location=location_name))
                return
            result = geo_data['results'][0]
            await get_routes_for_location(update.message.chat_id, result['latitude'], result['longitude'], context)
        except Exception as e:
            logger.error(f"路线查询失败: {e}")
            await update.effective_message.reply_text(_(user_id, "route_error"))

async def get_routes_for_location(chat_id: int, lat: float, lon: float, context: ContextTypes.DEFAULT_TYPE):
    google_maps_url = f"https://www.google.com/maps/@?api=1&map_action=map&center={lat},{lon}&zoom=14&layer=bicycling"
    komoot_url = f"https://www.komoot.com/plan/@{lat},{lon},14z"
    keyboard = [
        [InlineKeyboardButton(_(chat_id, "route_google_maps"), url=google_maps_url)],
        [InlineKeyboardButton(_(chat_id, "route_komoot"), url=komoot_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text=_(chat_id, "route_recommendation"), reply_markup=reply_markup)

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    location = update.effective_message.location
    context.user_data['location'] = location
    keyboard = [
        [InlineKeyboardButton(_(user_id, "location_button_weather"), callback_data="loc_weather"),
         InlineKeyboardButton(_(user_id, "location_button_route"), callback_data="loc_route")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(_(user_id, "location_received"), reply_markup=reply_markup)

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("English", callback_data="set_lang_en")],
        [InlineKeyboardButton("简体中文", callback_data="set_lang_zh-hans")],
        [InlineKeyboardButton("繁體中文", callback_data="set_lang_zh-hant")],
        [InlineKeyboardButton("Español", callback_data="set_lang_es")],
        [InlineKeyboardButton("Deutsch", callback_data="set_lang_de")],
        [InlineKeyboardButton("Français", callback_data="set_lang_fr")],
        [InlineKeyboardButton("Italiano", callback_data="set_lang_it")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(_(user_id, "language_prompt"), reply_markup=reply_markup)
    else:
        await update.effective_message.reply_text(_(user_id, "language_prompt"), reply_markup=reply_markup)
async def maintenance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if not context.args:
        # 列表显示模式
        cursor.execute("SELECT gear_id, name, distance FROM gear WHERE telegram_user_id = ?", (user_id,))
        gears = cursor.fetchall()
        if not gears:
            await update.effective_message.reply_text(_(user_id, "maintenance_no_gear"))
            conn.close()
            return
            
        msg_lines = [_(user_id, "maintenance_title")]
        for g_id, name, dist in gears:
            msg_lines.append(f"\n🚲 **{name}**")
            msg_lines.append(f"  ID: `{g_id}`")
            msg_lines.append(f"  {_(user_id, 'activity_detail_dist')}: {dist:.1f} km")
            
            # 显示保养项目
            cursor.execute("SELECT part_name, threshold_dist FROM maintenance WHERE gear_id = ?", (g_id,))
            parts = cursor.fetchall()
            for p_name, thresh in parts:
                msg_lines.append(f"  🛠 {p_name}: {thresh:.0f} km")
        
        msg_lines.append("\n💡 用法 / Usage:")
        msg_lines.append("`/maintenance ID PART THRESHOLD`\nEx: `/maintenance b123 Chain 3000`")
        if update.callback_query:
            await update.callback_query.edit_message_text("\n".join(msg_lines), parse_mode='Markdown')
        else:
            await update.effective_message.reply_text("\n".join(msg_lines), parse_mode='Markdown')
    else:
        # 设置模式: /maintenance ID PART THRESHOLD
        if len(context.args) < 3:
            await update.effective_message.reply_text("Usage: `/maintenance ID PART THRESHOLD`", parse_mode='Markdown')
        else:
            g_id, part, threshold = context.args[0], context.args[1], float(context.args[2])
            cursor.execute("SELECT name FROM gear WHERE gear_id = ? AND telegram_user_id = ?", (g_id, user_id))
            gear = cursor.fetchone()
            if not gear:
                await update.effective_message.reply_text("Gear ID error.")
            else:
                cursor.execute("INSERT OR REPLACE INTO maintenance (gear_id, part_name, threshold_dist, notified) VALUES (?, ?, ?, 0)", (g_id, part, threshold))
                conn.commit()
                await update.effective_message.reply_text(_(user_id, "maintenance_set_success").format(gear_name=gear[0], part=part, threshold=threshold))
    conn.close()

async def units_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("Metric (km/m)", callback_data="set_unit_metric")],
        [InlineKeyboardButton("Imperial (mi/ft)", callback_data="set_unit_imperial")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(_(user_id, "units_prompt"), reply_markup=reply_markup)
    else:
        await update.effective_message.reply_text(_(user_id, "units_prompt"), reply_markup=reply_markup)

async def set_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    unit = query.data.replace("set_unit_", "")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET units = ? WHERE telegram_user_id = ?", (unit, user_id))
    conn.commit()
    conn.close()
    
    await query.answer()
    await query.edit_message_text(_(user_id, "units_set_success").format(unit=unit))

async def add_rss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_message.chat_id
    
    # 在非私聊频道中检查管理员权限
    if update.effective_message.chat.type != 'private':
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ['administrator', 'creator']:
            await update.effective_message.reply_text("❌ 只有群管理员或群主才能添加 RSS 订阅。")
            return

    if not context.args:
        await update.effective_message.reply_text("用法 / Usage: `/add_rss URL`", parse_mode='Markdown')
        return
    url = context.args[0]
    chat_id = update.effective_message.chat_id
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. 确保 feed 记录存在
        cursor.execute("INSERT OR IGNORE INTO rss_feeds (url) VALUES (?)", (url,))
        cursor.execute("SELECT feed_id FROM rss_feeds WHERE url = ?", (url,))
        feed_id = cursor.fetchone()[0]
        
        # 2. 建立订阅关系
        cursor.execute("INSERT INTO rss_subscriptions (feed_id, chat_id) VALUES (?, ?)", (feed_id, chat_id))
        conn.commit()
        await update.effective_message.reply_text("✅ RSS 订阅成功！")
    except sqlite3.IntegrityError:
        await update.effective_message.reply_text("⚠️ 该群内已存在此 RSS 订阅。")
    finally:
        conn.close()

async def list_rss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_message.chat_id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.feed_id, f.url FROM rss_feeds f
        JOIN rss_subscriptions s ON f.feed_id = s.feed_id
        WHERE s.chat_id = ?
    """, (chat_id,))
    feeds = cursor.fetchall()
    conn.close()
    if not feeds:
        await update.effective_message.reply_text("目前没有订阅任何 RSS 源。")
        return
    msg = "**当前订阅的 RSS 源：**\n"
    for f_id, url in feeds:
        msg += f"- `{f_id}`: {url}\n"
    msg += "\n删除订阅使用: `/remove_rss ID`"
    await update.effective_message.reply_text(msg, parse_mode='Markdown')

async def remove_rss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type != 'private':
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ['administrator', 'creator']:
            await update.effective_message.reply_text("❌ 只有群管理员或群主才能删除 RSS 订阅。")
            return

    if not context.args:
        await update.effective_message.reply_text("用法 / Usage: `/remove_rss ID`", parse_mode='Markdown')
        return
    feed_id = context.args[0]
    conn = get_db_connection()
    cursor = conn.cursor()
    # 仅删除当前群组的订阅关系
    cursor.execute("DELETE FROM rss_subscriptions WHERE feed_id = ? AND chat_id = ?", (feed_id, chat_id))
    conn.commit()
    conn.close()
    await update.effective_message.reply_text("🗑 RSS 订阅已删除。")

async def sync_strava_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """手动触发 Strava 数据同步"""
    user_id = update.effective_user.id
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_user_id, strava_access_token, strava_refresh_token, strava_token_expires_at, strava_last_activity_ts, strava_notification_mode FROM users WHERE telegram_user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        await update.effective_message.reply_text(_(user_id, "privacy_not_linked"))
        conn.close()
        return

    msg = await update.effective_message.reply_text(_(user_id, "sync_started"))
    
    try:
        from src.bot.tasks import process_single_user_sync
        from stravalib.client import Client
        client = Client()
        await process_single_user_sync(user, client, cursor, conn, context)
        await msg.edit_text(_(user_id, "sync_success"))
    except Exception as e:
        logger.error(f"手动同步失败: {e}")
        await msg.edit_text(f"❌ 同步失败: {e}")
    finally:
        conn.close()

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = f"⚙️ **VeloBot {_(user_id, 'menu_title')}**\n\n{_(user_id, 'menu_subtitle')}"
    
    keyboard = [
        [
            InlineKeyboardButton(f"🚴 {_(user_id, 'menu_activity')}", callback_data="menu_activity"),
            InlineKeyboardButton(f"🏆 {_(user_id, 'menu_stats')}", callback_data="menu_stats")
        ],
        [
            InlineKeyboardButton(f"🔧 {_(user_id, 'menu_gear')}", callback_data="menu_gear"),
            InlineKeyboardButton(f"🏅 {_(user_id, 'menu_awards')}", callback_data="menu_awards")
        ],
        [
            InlineKeyboardButton(f"🌍 {_(user_id, 'menu_tools')}", callback_data="menu_tools"),
            InlineKeyboardButton(f"⚙️ {_(user_id, 'menu_settings')}", callback_data="menu_settings")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.effective_message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def set_ftp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("使用方式: `/set_ftp 200` (请替换为你的实际 FTP 值)", parse_mode='Markdown')
        return
    try:
        ftp = int(context.args[0])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET ftp = ? WHERE telegram_user_id = ?", (ftp, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"✅ FTP 已更新为: {ftp} W")
    except ValueError:
        await update.message.reply_text("❌ 请输入有效的数字。")

async def set_max_hr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("使用方式: `/set_max_hr 190` (请替换为你的实际 最大心率 值)", parse_mode='Markdown')
        return
    try:
        hr = int(context.args[0])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET max_hr = ? WHERE telegram_user_id = ?", (hr, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"✅ 最大心率 已更新为: {hr} bpm")
    except ValueError:
        await update.message.reply_text("❌ 请输入有效的数字。")

async def ai_coach_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.effective_message.text
    replied_msg = update.effective_message.reply_to_message
    
    # 基础用户数据
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ftp, max_hr FROM users WHERE telegram_user_id = ?", (user_id,))
    u_data = cursor.fetchone()
    user_config = {"ftp": u_data[0], "max_hr": u_data[1]} if u_data else {"ftp": 200, "max_hr": 190}

    activity_context = ""
    # 尝试识别回复内容中的活动 ID
    if replied_msg:
        # 从消息文本中查找 Strava 链接
        strava_match = re.search(r'strava\.com/activities/(\d+)', replied_msg.text or replied_msg.caption or "")
        if strava_match:
            act_id = strava_match.group(1)
            cursor.execute("SELECT distance, moving_time, elevation_gain, suffer_score, avg_hr, tss, np, if_score FROM activities WHERE activity_id = ?", (act_id,))
            a_res = cursor.fetchone()
            if a_res:
                activity_context = (
                    f"此活动的数据: 距离 {a_res[0]:.2f}km, 时间 {format_duration(a_res[1])}, 爬升 {a_res[2]}m, "
                    f"受累分 {a_res[3]}, 平均心率 {a_res[4]}, TSS {a_res[5]}, NP {a_res[6]}, IF {a_res[7]}。"
                )
    
    # 如果是私聊且没回复特定消息，尝试获取最近一次活动
    if not activity_context and update.effective_chat.type == Chat.PRIVATE:
        cursor.execute("SELECT distance, moving_time, elevation_gain, suffer_score, avg_hr, tss, np, if_score FROM activities WHERE telegram_user_id = ? ORDER BY start_date DESC LIMIT 1", (user_id,))
        a_res = cursor.fetchone()
        if a_res:
            activity_context = (
                f"你最近一次活动的数据: 距离 {a_res[0]:.2f}km, 时间 {format_duration(a_res[1])}, 爬升 {a_res[2]}m, "
                f"TSS {a_res[5]}, NP {a_res[6]}, IF {a_res[7]}。"
            )

    conn.close()

    if not query: return

    # 发送一个“思考中”的提示
    waiting_msg = await update.effective_message.reply_text("🤔 Velo Coach 正在分析数据，请稍候...", parse_mode='Markdown')
    
    response = await ask_ai_coach(query, user_data=user_config, activity_data=activity_context)
    
    await context.bot.edit_message_text(chat_id=user_id, message_id=waiting_msg.message_id, text=response, parse_mode='Markdown')

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    voice = update.message.voice
    
    waiting_msg = await update.effective_message.reply_text("🎤 正在识别您的语音并进行回复...", parse_mode='Markdown')
    
    file = await context.bot.get_file(voice.file_id)
    os.makedirs("temp", exist_ok=True)
    file_path = f"temp/voice_{user_id}_{int(datetime.now().timestamp())}.ogg"
    await file.download_to_drive(file_path)
    
    transcription = await transcribe_voice(file_path)
    if os.path.exists(file_path): os.remove(file_path)

    if transcription:
        # 复用 AI coach 逻辑
        update.effective_message.text = transcription # 伪造 text 供后续使用
        await ai_coach_handler(update, context)
    else:
        await context.bot.edit_message_text(chat_id=user_id, message_id=waiting_msg.message_id, text="❌ 语音识别失败，请确保录音清晰。")

async def set_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("使用方式: `/set_goal 500` (设置每月骑行目标里程，单位 km)", parse_mode='Markdown')
        return
    try:
        goal = float(context.args[0])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET monthly_goal_dist = ? WHERE telegram_user_id = ?", (goal, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"✅ 每月目标里程已设置为: {goal} km。加油，骑手！")
    except ValueError:
        await update.message.reply_text("❌ 请输入有效的数字。")

async def set_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    usage = "使用方式: `/set_schedule sat 08:00 sun 09:00` (设置你习惯的骑行时间)"
    if not context.args or len(context.args) % 2 != 0:
        await update.message.reply_text(usage, parse_mode='Markdown')
        return
    
    schedule = {}
    valid_days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    try:
        for i in range(0, len(context.args), 2):
            day = context.args[i].lower()
            time = context.args[i+1]
            if day not in valid_days:
                raise ValueError(f"无效的星期: {day}")
            # 简单验证时间格式 HH:MM
            if not re.match(r'^\d{2}:\d{2}$', time):
                raise ValueError(f"无效的时间格式: {time}")
            schedule[day] = time
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET riding_schedule = ? WHERE telegram_user_id = ?", (json.dumps(schedule), user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"✅ 习惯骑行时间已更新: {schedule}\n机器人将在计划骑行的前一晚为你提供天气预警。")
    except ValueError as e:
        await update.message.reply_text(f"❌ 设置失败: {e}")
