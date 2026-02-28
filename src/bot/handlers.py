import sqlite3
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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

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
    authorize_url = client.authorization_url(client_id=STRAVA_CLIENT_ID, redirect_uri=redirect_uri, scope=['read', 'activity:read'], state=str(user_id))
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
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    current_period_start = today - timedelta(days=7)
    previous_period_start = current_period_start - timedelta(days=7)
    conn = get_db_connection()
    cursor = conn.cursor()
    def query_stats(start_ts, end_ts):
        cursor.execute("SELECT COUNT(*), SUM(distance), SUM(moving_time), SUM(elevation_gain) FROM activities WHERE telegram_user_id = ? AND start_date >= ? AND start_date < ?", (user_id, start_ts, end_ts))
        return cursor.fetchone()
    current_stats = query_stats(current_period_start.timestamp(), today.timestamp())
    previous_stats = query_stats(previous_period_start.timestamp(), current_period_start.timestamp())
    conn.close()
    if not current_stats or not current_stats[0]:
        await update.effective_message.reply_text(_(user_id, "report_no_activity"), parse_mode='Markdown')
        return
    c_count, c_dist, c_time, c_elev = current_stats
    p_count, p_dist, p_time, p_elev = previous_stats if previous_stats else (0, 0, 0, 0)
    def format_comparison(current, previous):
        if previous is None or previous == 0: return ""
        current, previous = current or 0, previous or 0
        diff = ((current - previous) / previous) * 100
        return f" `({'+' if diff >= 0 else ''}{diff:.0f}%)`"
    
    message = [
        _(user_id, "report_title"),
        _(user_id, "report_rides").format(count=c_count, comparison=format_comparison(c_count, p_count)),
        _(user_id, "report_dist").format(dist=(c_dist or 0), comparison=format_comparison(c_dist, p_dist)),
        _(user_id, "report_time").format(time=format_duration(c_time or 0), comparison=format_comparison(c_time, p_time)),
        _(user_id, "report_elev").format(elev=(c_elev or 0), comparison=format_comparison(c_elev, p_elev))
    ]
    
    # 生成 Suffer Score 趋势图
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date(start_date, 'unixepoch', 'localtime') as day, SUM(suffer_score) 
        FROM activities 
        WHERE telegram_user_id = ? AND start_date >= ? 
        GROUP BY day ORDER BY day ASC
    """, (user_id, current_period_start.timestamp()))
    trend_data = cursor.fetchall()
    conn.close()
    
    if trend_data:
        dates = [row[0][5:] for row in trend_data]  # 仅保留 MM-DD
        scores = [row[1] or 0 for row in trend_data]
        trend_path = await generate_suffer_trend(user_id, dates, scores)
        if trend_path:
            await update.effective_message.reply_photo(photo=open(trend_path, 'rb'), caption="\n".join(message), parse_mode='Markdown')
            return

    await update.effective_message.reply_text("\n".join(message), parse_mode='Markdown')

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
    for ach_id, _ in LOCALIZED_ACHIEVEMENTS['en'].items():
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
