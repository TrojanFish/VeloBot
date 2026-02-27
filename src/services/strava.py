import sqlite3
import logging
from datetime import datetime, timezone
from src.config import DB_FILE
from src.utils import _, format_duration, get_achievement_text, get_user_units, convert_dist, convert_elev, convert_speed
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

def format_activity_details(activity, user_id):
    units = get_user_units(user_id)
    details = []
    
    # Suffer Score
    suffer_score = getattr(activity, 'suffer_score', None)
    if suffer_score:
        if suffer_score > 300: details.append(_(user_id, "activity_suffer_intense"))
        elif suffer_score > 150: details.append(_(user_id, "activity_suffer_high"))
        elif suffer_score > 50: details.append(_(user_id, "activity_suffer_medium"))
        else: details.append(_(user_id, "activity_suffer_easy"))
        
    if str(activity.type) == 'Ride':
        dist_km = float(activity.distance) / 1000 if activity.distance else 0
        elev_m = float(activity.total_elevation_gain) if activity.total_elevation_gain else 0
        if dist_km > 0:
            ratio = elev_m / dist_km
            if ratio > 20: details.append(_(user_id, "activity_type_climb"))
            elif ratio > 8: details.append(_(user_id, "activity_type_hilly"))
            else: details.append(_(user_id, "activity_type_flat"))
    
    # 核心数据转换
    dist_str = convert_dist(float(activity.distance)/1000, units) if activity.distance else "0.00 km"
    elev_str = convert_elev(float(activity.total_elevation_gain), units) if activity.total_elevation_gain else "0 m"
    
    details.extend([
        f"{_(user_id, 'activity_detail_dist')}: {dist_str}",
        f"{_(user_id, 'activity_detail_time')}: {format_duration(float(activity.moving_time))}" if activity.moving_time else f"{_(user_id, 'activity_detail_time')}: 0:00:00",
        f"{_(user_id, 'activity_detail_elev')}: {elev_str}"
    ])
    
    if activity.average_speed:
        avg_speed_str = convert_speed(float(activity.average_speed) * 3.6, units)
        details.append(f"{_(user_id, 'activity_detail_avg_speed')}: {avg_speed_str}")
        
    if activity.max_speed:
        max_speed_str = convert_speed(float(activity.max_speed) * 3.6, units)
        details.append(f"{_(user_id, 'activity_detail_max_speed')}: {max_speed_str}")

    avg_hr = getattr(activity, 'average_heartrate', None)
    if avg_hr: details.append(f"{_(user_id, 'activity_detail_avg_hr')}: {avg_hr:.0f} bpm")
    
    calories = getattr(activity, 'calories', None)
    if calories: details.append(f"{_(user_id, 'activity_detail_calories')}: {calories:.0f} kcal")
    
    avg_watts = getattr(activity, 'average_watts', None)
    device_watts = getattr(activity, 'device_watts', False)
    if avg_watts and device_watts: details.append(f"{_(user_id, 'activity_detail_avg_power')}: {avg_watts:.0f} W")
    
    avg_cadence = getattr(activity, 'average_cadence', None)
    if avg_cadence:
        act_type = str(activity.type)
        details.append(f"{_(user_id, 'activity_detail_avg_cadence')}: {avg_cadence * 2 if act_type == 'Run' else avg_cadence:.0f} {'rpm' if act_type == 'Ride' else 'spm'}")
    
    if suffer_score: details.append(f"{_(user_id, 'activity_detail_suffer_score')}: {suffer_score:.0f}")
    
    # 添加器材信息 (如果是公开推送，由于 handlers 外部已经获取了 gear，这里可能需要传入)
    # 但由于 activity 对象本身有 gear_id，我们可以以后在任务中处理。
    
    return details

async def check_and_grant_achievements(user_id, activity, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT achievement_id FROM achievements WHERE telegram_user_id = ?", (user_id,))
    unlocked_ids = {row[0] for row in cursor.fetchall()}
    newly_unlocked = []
    
    # 基础成就
    if 'dist_100k' not in unlocked_ids and float(activity.distance) / 1000 >= 100: newly_unlocked.append('dist_100k')
    if 'elev_1000m' not in unlocked_ids and float(activity.total_elevation_gain) >= 1000: newly_unlocked.append('elev_1000m')
    if 'max_speed_70k' not in unlocked_ids and float(activity.max_speed) * 3.6 >= 70: newly_unlocked.append('max_speed_70k')
    if 'elev_2000m' not in unlocked_ids and float(activity.total_elevation_gain) >= 2000: newly_unlocked.append('elev_2000m')

    # 累积成就 (所有时间)
    cursor.execute("SELECT SUM(distance) FROM activities WHERE telegram_user_id = ?", (user_id,))
    total_distance = (cursor.fetchone()[0] or 0)
    if 'total_dist_1000k' not in unlocked_ids and total_distance >= 1000: newly_unlocked.append('total_dist_1000k')
    if 'total_dist_5000k' not in unlocked_ids and total_distance >= 5000: newly_unlocked.append('total_dist_5000k')
    if 'total_dist_10000k' not in unlocked_ids and total_distance >= 10000: newly_unlocked.append('total_dist_10000k')
    
    # 周期成就 (月度/年度)
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).timestamp()
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).timestamp()
    
    cursor.execute("SELECT SUM(distance) FROM activities WHERE telegram_user_id = ? AND start_date >= ?", (user_id, month_start))
    month_dist = (cursor.fetchone()[0] or 0)
    if 'month_dist_500k' not in unlocked_ids and month_dist >= 500: newly_unlocked.append('month_dist_500k')
    
    cursor.execute("SELECT SUM(distance) FROM activities WHERE telegram_user_id = ? AND start_date >= ?", (user_id, year_start))
    year_dist = (cursor.fetchone()[0] or 0)
    if 'year_dist_10000k' not in unlocked_ids and year_dist >= 10000: newly_unlocked.append('year_dist_10000k')
    
    now_ts = int(datetime.now(timezone.utc).timestamp())
    for achievement_id in newly_unlocked:
        cursor.execute("INSERT INTO achievements VALUES (?, ?, ?)", (user_id, achievement_id, now_ts))
        conn.commit()
        achievement = get_achievement_text(user_id, achievement_id)
        message = _(user_id, "achievement_unlocked").format(name=achievement['name'], desc=achievement['desc'])
        await context.bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')
    conn.close()
