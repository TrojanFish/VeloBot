import sqlite3
import logging
from datetime import datetime, timezone
from src.config import DB_FILE
from src.utils import _, format_duration, get_achievement_text
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

def format_activity_details(activity, user_id):
    details = []
    if activity.suffer_score:
        score = activity.suffer_score
        if score > 300: details.append(_(user_id, "activity_suffer_intense"))
        elif score > 150: details.append(_(user_id, "activity_suffer_high"))
        elif score > 50: details.append(_(user_id, "activity_suffer_medium"))
        else: details.append(_(user_id, "activity_suffer_easy"))
    if str(activity.type) == 'Ride':
        dist_km = float(activity.distance) / 1000 if activity.distance else 0
        elev_m = float(activity.total_elevation_gain) if activity.total_elevation_gain else 0
        if dist_km > 0:
            ratio = elev_m / dist_km
            if ratio > 20: details.append(_(user_id, "activity_type_climb"))
            elif ratio > 8: details.append(_(user_id, "activity_type_hilly"))
            else: details.append(_(user_id, "activity_type_flat"))
    
    details.extend([
        f"{_(user_id, 'activity_detail_dist')}: {float(activity.distance)/1000:.2f} km" if activity.distance else f"{_(user_id, 'activity_detail_dist')}: 0.00 km",
        f"{_(user_id, 'activity_detail_time')}: {format_duration(float(activity.moving_time))}" if activity.moving_time else f"{_(user_id, 'activity_detail_time')}: 0:00:00",
        f"{_(user_id, 'activity_detail_elev')}: {float(activity.total_elevation_gain):.0f} m" if activity.total_elevation_gain else f"{_(user_id, 'activity_detail_elev')}: 0 m"
    ])
    if activity.average_speed:
        avg_speed_kmh = float(activity.average_speed) * 3.6
        if avg_speed_kmh > 0: details.append(f"{_(user_id, 'activity_detail_avg_speed')}: {avg_speed_kmh:.1f} km/h")
    if activity.max_speed:
        max_speed_kmh = float(activity.max_speed) * 3.6
        if max_speed_kmh > 0: details.append(f"{_(user_id, 'activity_detail_max_speed')}: {max_speed_kmh:.1f} km/h")
    if activity.average_heartrate: details.append(f"{_(user_id, 'activity_detail_avg_hr')}: {activity.average_heartrate:.0f} bpm")
    if activity.calories: details.append(f"{_(user_id, 'activity_detail_calories')}: {activity.calories:.0f} kcal")
    if activity.average_watts and activity.device_watts: details.append(f"{_(user_id, 'activity_detail_avg_power')}: {activity.average_watts:.0f} W")
    if activity.average_cadence: details.append(f"{_(user_id, 'activity_detail_avg_cadence')}: {activity.average_cadence * 2 if activity.type == 'Run' else activity.average_cadence:.0f} {'rpm' if activity.type == 'Ride' else 'spm'}")
    if activity.suffer_score: details.append(f"{_(user_id, 'activity_detail_suffer_score')}: {activity.suffer_score:.0f}")
    return details

async def check_and_grant_achievements(user_id, activity, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT achievement_id FROM achievements WHERE telegram_user_id = ?", (user_id,))
    unlocked_ids = {row[0] for row in cursor.fetchall()}
    newly_unlocked = []
    if 'dist_100k' not in unlocked_ids and float(activity.distance) / 1000 >= 100: newly_unlocked.append('dist_100k')
    if 'elev_1000m' not in unlocked_ids and float(activity.total_elevation_gain) >= 1000: newly_unlocked.append('elev_1000m')
    if 'max_speed_70k' not in unlocked_ids and float(activity.max_speed) * 3.6 >= 70: newly_unlocked.append('max_speed_70k')
    cursor.execute("SELECT SUM(distance) FROM activities WHERE telegram_user_id = ?", (user_id,))
    total_distance = (cursor.fetchone()[0] or 0)
    if 'total_dist_1000k' not in unlocked_ids and total_distance >= 1000: newly_unlocked.append('total_dist_1000k')
    if 'total_dist_5000k' not in unlocked_ids and total_distance >= 5000: newly_unlocked.append('total_dist_5000k')
    now_ts = int(datetime.now(timezone.utc).timestamp())
    for achievement_id in newly_unlocked:
        cursor.execute("INSERT INTO achievements VALUES (?, ?, ?)", (user_id, achievement_id, now_ts))
        conn.commit()
        achievement = get_achievement_text(user_id, achievement_id)
        message = _(user_id, "achievement_unlocked").format(name=achievement['name'], desc=achievement['desc'])
        await context.bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')
    conn.close()
