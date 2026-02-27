import sqlite3
import logging
from datetime import datetime, timezone
from src.config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, TELEGRAM_CHAT_ID, DB_FILE
from src.utils import _, format_duration
from src.services.strava import format_activity_details, check_and_grant_achievements
from stravalib.client import Client
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def check_strava_activities(context: ContextTypes.DEFAULT_TYPE):
    logger.info("开始检查 Strava 活动更新...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_user_id, strava_access_token, strava_refresh_token, strava_token_expires_at, strava_last_activity_ts, strava_notification_mode FROM users WHERE strava_access_token IS NOT NULL")
    users = cursor.fetchall()
    client = Client()
    for user in users:
        (telegram_user_id, access_token, refresh_token, expires_at, last_activity_ts, notification_mode) = user
        try:
            if datetime.now(timezone.utc).timestamp() > expires_at:
                response = client.refresh_access_token(client_id=STRAVA_CLIENT_ID, client_secret=STRAVA_CLIENT_SECRET, refresh_token=refresh_token)
                access_token, refresh_token, expires_at = response['access_token'], response['refresh_token'], response['expires_at']
                cursor.execute('UPDATE users SET strava_access_token=?, strava_refresh_token=?, strava_token_expires_at=? WHERE telegram_user_id=?', (access_token, refresh_token, expires_at, telegram_user_id))
                conn.commit()
            client.access_token = access_token
            athlete = client.get_athlete()
            activities = client.get_activities(after=datetime.fromtimestamp(last_activity_ts, tz=timezone.utc))
            new_activities = sorted(list(activities), key=lambda a: a.start_date)
            if not new_activities: continue
            
            for activity in new_activities:
                logger.info(f"发现用户 {athlete.firstname} 的新活动: {activity.name}")
                cursor.execute("INSERT OR IGNORE INTO activities (activity_id, telegram_user_id, start_date, distance, moving_time, elevation_gain) VALUES (?, ?, ?, ?, ?, ?)", 
                               (activity.id, telegram_user_id, activity.start_date.timestamp(), float(activity.distance) / 1000, activity.moving_time.total_seconds(), float(activity.total_elevation_gain)))
                conn.commit()
                await check_and_grant_achievements(telegram_user_id, activity, context)
                activity_type_emoji = {"Ride": "🚴", "Run": "🏃", "Swim": "🏊", "Walk": "🚶", "Hike": "⛰️", "AlpineSki": "⛷️", "Workout": "💪", "Yoga": "🧘", "VirtualRide": "💻🚴"}.get(str(activity.type), "🏆")
                
                message_lines = [f"{activity_type_emoji} **{athlete.firstname} {athlete.lastname}** has completed a new activity!\n", f"**{activity.name}**"]
                message_lines.extend(format_activity_details(activity, telegram_user_id))
                message_lines.append(f"\n🔗 [{_(telegram_user_id, 'activity_view_on_strava')}](https://www.strava.com/activities/{activity.id})")
                
                message = "\n".join(message_lines)
                target_chat_id = TELEGRAM_CHAT_ID if notification_mode == 'public' else telegram_user_id
                await context.bot.send_message(chat_id=target_chat_id, text=message, parse_mode='Markdown')
            
            latest_activity_ts = int(new_activities[-1].start_date.timestamp())
            cursor.execute("UPDATE users SET strava_last_activity_ts=? WHERE telegram_user_id=?", (latest_activity_ts, telegram_user_id))
            conn.commit()
        except Exception as e:
            logger.error(f"处理用户 {telegram_user_id} 的 Strava 数据时出错: {e}")
            if "Authorization Error" in str(e):
                await context.bot.send_message(chat_id=telegram_user_id, text=_(telegram_user_id, "reauth_required"))
    conn.close()
