import sqlite3
import logging
from datetime import datetime, timezone
from src.config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, TELEGRAM_CHAT_ID, DB_FILE
from src.utils import _, format_duration
from src.services.strava import format_activity_details, check_and_grant_achievements
from src.services.feishu import send_feishu_notification
from src.services.visuals import generate_static_map, generate_elevation_profile
from stravalib.client import Client
from telegram import InputMediaPhoto
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def sync_athlete_gear(client, telegram_user_id, cursor):
    """同步运动员的器材信息"""
    try:
        athlete = client.get_athlete()
        gears = []
        if athlete.bikes: gears.extend(athlete.bikes)
        if athlete.shoes: gears.extend(athlete.shoes)
        
        for g in gears:
            # 获取详细信息以获取品牌和型号
            g_detail = client.get_gear(g.id)
            cursor.execute('''
                INSERT OR REPLACE INTO gear (gear_id, telegram_user_id, name, brand_name, model_name, distance, is_primary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (g_detail.id, telegram_user_id, g_detail.name, g_detail.brand_name, g_detail.model_name, float(g_detail.distance)/1000, 1 if g_detail.primary else 0))
    except Exception as e:
        logger.error(f"同步器材信息失败: {e}")

async def check_maintenance_alerts(telegram_user_id, context, cursor):
    """检查是否有器材需要保养"""
    cursor.execute('''
        SELECT g.name, m.part_name, g.distance, m.threshold_dist, m.id
        FROM gear g JOIN maintenance m ON g.gear_id = m.gear_id
        WHERE g.telegram_user_id = ? AND g.distance >= m.threshold_dist AND m.notified = 0
    ''', (telegram_user_id,))
    alerts = cursor.fetchall()
    for alert in alerts:
        gear_name, part_name, current_dist, threshold, m_id = alert
        msg = f"⚠️ **保养提醒 / Maintenance Alert**\n\n您的器材 **{gear_name}** 的 **{part_name}** 已达到保养阈值！\n当前里程: {current_dist:.1f} km\n设定阈值: {threshold:.1f} km\n\n请及时维护以确保安全。"
        await context.bot.send_message(chat_id=telegram_user_id, text=msg, parse_mode='Markdown')
        cursor.execute("UPDATE maintenance SET notified = 1 WHERE id = ?", (m_id,))

async def sync_user_data(context: ContextTypes.DEFAULT_TYPE):
    """同步特定用户的数据 (用于授权后立即同步)"""
    job_data = context.job.data
    telegram_user_id = job_data['telegram_user_id']
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_user_id, strava_access_token, strava_refresh_token, strava_token_expires_at, strava_last_activity_ts, strava_notification_mode FROM users WHERE telegram_user_id = ?", (telegram_user_id,))
    user = cursor.fetchone()
    if user:
        client = Client()
        await process_single_user_sync(user, client, cursor, conn, context)
    conn.close()

async def process_single_user_sync(user, client, cursor, conn, context):
    (telegram_user_id, access_token, refresh_token, expires_at, last_activity_ts, notification_mode) = user
    try:
        if datetime.now(timezone.utc).timestamp() > expires_at:
            response = client.refresh_access_token(client_id=STRAVA_CLIENT_ID, client_secret=STRAVA_CLIENT_SECRET, refresh_token=refresh_token)
            access_token, refresh_token, expires_at = response['access_token'], response['refresh_token'], response['expires_at']
            cursor.execute('UPDATE users SET strava_access_token=?, strava_refresh_token=?, strava_token_expires_at=? WHERE telegram_user_id=?', (access_token, refresh_token, expires_at, telegram_user_id))
            conn.commit()
        client.access_token = access_token
        
        # 同步器材
        await sync_athlete_gear(client, telegram_user_id, cursor)
        conn.commit()

        athlete = client.get_athlete()
        # 如果是第一次同步，拉取过去 30 天的活动，而不是只拉取之后的新活动
        if last_activity_ts == 0:
            from datetime import timedelta
            after_ts = (datetime.now(timezone.utc) - timedelta(days=30)).timestamp()
        else:
            after_ts = last_activity_ts

        activities = client.get_activities(after=datetime.fromtimestamp(after_ts, tz=timezone.utc))
        new_activities = sorted(list(activities), key=lambda a: a.start_date)
        
        for activity in new_activities:
            # 查重
            cursor.execute("SELECT 1 FROM activities WHERE activity_id = ?", (activity.id,))
            if cursor.fetchone(): continue
            
            logger.info(f"发现用户 {athlete.firstname} 的新活动: {activity.name}")
            
            # 获取更多数据
            suffer = getattr(activity, 'suffer_score', None)
            hr = getattr(activity, 'average_heartrate', None)
            gear_id = getattr(activity, 'gear_id', None)
            
            cursor.execute('''
                INSERT OR IGNORE INTO activities 
                (activity_id, telegram_user_id, start_date, distance, moving_time, elevation_gain, suffer_score, avg_hr, gear_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (activity.id, telegram_user_id, activity.start_date.timestamp(), 
                  float(activity.distance) / 1000, float(activity.moving_time) if activity.moving_time else 0, 
                  float(activity.total_elevation_gain), suffer, hr, gear_id))
            conn.commit()
            
            await check_and_grant_achievements(telegram_user_id, activity, context)
            
            # 检查保养提醒
            await check_maintenance_alerts(telegram_user_id, context, cursor)
            conn.commit()

            activity_type_emoji = {"Ride": "🚴", "Run": "🏃", "Swim": "🏊", "Walk": "🚶", "Hike": "⛰️", "AlpineSki": "⛷️", "Workout": "💪", "Yoga": "🧘", "VirtualRide": "💻🚴"}.get(str(activity.type), "🏆")
            
            message_lines = [f"{activity_type_emoji} **{athlete.firstname} {athlete.lastname}** has completed a new activity!\n", f"**{activity.name}**"]
            message_lines.extend(format_activity_details(activity, telegram_user_id))
            
            if gear_id:
                cursor.execute("SELECT name FROM gear WHERE gear_id = ?", (gear_id,))
                g_res = cursor.fetchone()
                if g_res: message_lines.append(f"🚲 **{g_res[0]}**")
            
            message_lines.append(f"\n🔗 [{_(telegram_user_id, 'activity_view_on_strava')}](https://www.strava.com/activities/{activity.id})")
            
            message = "\n".join(message_lines)
            target_chat_id = TELEGRAM_CHAT_ID if notification_mode == 'public' else telegram_user_id
            
            media = []
            if hasattr(activity, 'map') and activity.map.summary_polyline:
                map_path = await generate_static_map(activity.id, activity.map.summary_polyline)
                if map_path: media.append(InputMediaPhoto(open(map_path, 'rb')))
            
            if float(activity.total_elevation_gain) > 50:
                try:
                    streams = client.get_activity_streams(activity.id, types=['altitude', 'distance'])
                    elev_path = await generate_elevation_profile(activity.id, streams)
                    if elev_path: media.append(InputMediaPhoto(open(elev_path, 'rb')))
                except: pass
            
            if media:
                media[0].caption = message
                media[0].parse_mode = 'Markdown'
                await context.bot.send_media_group(chat_id=target_chat_id, media=media)
            else:
                await context.bot.send_message(chat_id=target_chat_id, text=message, parse_mode='Markdown')
            
            if notification_mode == 'public':
                await send_feishu_notification(f"Strava 新活动: {athlete.firstname} {athlete.lastname}", message)
        
        if new_activities:
            latest_activity_ts = int(new_activities[-1].start_date.timestamp())
            cursor.execute("UPDATE users SET strava_last_activity_ts=? WHERE telegram_user_id=?", (latest_activity_ts, telegram_user_id))
            conn.commit()
    except Exception as e:
        logger.error(f"处理用户 {telegram_user_id} 的 Strava 数据时出错: {e}")
        if "Authorization Error" in str(e):
            await context.bot.send_message(chat_id=telegram_user_id, text=_(telegram_user_id, "reauth_required"))

async def check_strava_activities(context: ContextTypes.DEFAULT_TYPE):
    logger.info("开始检查 Strava 活动更新...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_user_id, strava_access_token, strava_refresh_token, strava_token_expires_at, strava_last_activity_ts, strava_notification_mode FROM users WHERE strava_access_token IS NOT NULL")
    users = cursor.fetchall()
    client = Client()
    for user in users:
        await process_single_user_sync(user, client, cursor, conn, context)
    conn.close()
