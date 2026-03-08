import sqlite3
import json
import logging
from datetime import datetime, timezone, timedelta
from src.config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, TELEGRAM_CHAT_ID, DB_FILE
from src.utils import _, format_duration
from src.services.strava import format_activity_details, check_and_grant_achievements
from src.services.feishu import send_feishu_notification
from src.services.visuals import generate_static_map, generate_elevation_profile
from stravalib.client import Client
from telegram import InputMediaPhoto, Bot
from telegram.ext import ContextTypes, Application
from src.services.visuals import generate_static_map, generate_elevation_profile, generate_suffer_trend
from src.services.metrics import calculate_tss, generate_zone_chart, get_tss_feedback
from src.services.weather import get_weather_for_city

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
    # 获取 FTP 和 心率设置
    cursor.execute("SELECT ftp, max_hr FROM users WHERE telegram_user_id = ?", (telegram_user_id,))
    u_config = cursor.fetchone()
    user_ftp, user_max_hr = u_config if u_config else (200, 190)
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
        if not last_activity_ts:
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
            
            # 获取更多详细数据 (Summary 数据可能不全)
            full_activity = client.get_activity(activity.id)
            tss, np, if_score = calculate_tss(full_activity, user_ftp, user_max_hr)
            
            suffer = getattr(full_activity, 'suffer_score', None)
            hr = getattr(full_activity, 'average_heartrate', None)
            gear_id = getattr(full_activity, 'gear_id', None)
            
            cursor.execute('''
                INSERT OR IGNORE INTO activities 
                (activity_id, telegram_user_id, start_date, distance, moving_time, elevation_gain, suffer_score, avg_hr, gear_id, tss, np, if_score) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (activity.id, telegram_user_id, activity.start_date.timestamp(), 
                  float(activity.distance) / 1000, float(activity.moving_time) if activity.moving_time else 0, 
                  float(activity.total_elevation_gain), suffer, hr, gear_id, tss, np, if_score))
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
            
            if tss > 0:
                message_lines.append(f"🎯 **TSS**: {tss:.1f} (IF: {if_score:.2f})")
            
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
            
            # 引入：区间分布图
            try:
                zones = client.get_activity_zones(activity.id)
                if zones:
                    zone_path = await generate_zone_chart(telegram_user_id, zones)
                    if zone_path: media.append(InputMediaPhoto(open(zone_path, 'rb')))
            except Exception as e:
                logger.debug(f"获取区间数据失败: {e}")
            
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


async def generate_and_send_user_report(user_id, bot: Bot, report_type: str = 'weekly'):
    """生成并发送个人报表"""
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if report_type == 'weekly':
        end = today
        start = end - timedelta(days=7)
        p_end = start
        p_start = p_end - timedelta(days=7)
        title_key = "report_title"
        no_act_key = "report_no_activity"
    elif report_type == 'monthly':
        end = today.replace(day=1)
        last_month = end - timedelta(days=1)
        start = last_month.replace(day=1)
        p_end = start
        p_start = (p_end - timedelta(days=1)).replace(day=1)
        title_key = "report_monthly_title"
        no_act_key = "report_monthly_no_activity"
    elif report_type == 'yearly':
        end = today.replace(month=1, day=1)
        start = end.replace(year=end.year - 1)
        p_end = start
        p_start = p_end.replace(year=p_end.year - 1)
        title_key = "report_yearly_title"
        no_act_key = "report_yearly_no_activity"
    else: # Default behavior for command on-demand (last 7 days)
        end = today
        start = end - timedelta(days=7)
        p_end = start
        p_start = p_end - timedelta(days=7)
        title_key = "report_title"
        no_act_key = "report_no_activity"

    from src.database import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    def query_stats(s_ts, e_ts):
        cursor.execute("SELECT COUNT(*), SUM(distance), SUM(moving_time), SUM(elevation_gain), SUM(tss) FROM activities WHERE telegram_user_id = ? AND start_date >= ? AND start_date < ?", (user_id, s_ts, e_ts))
        return cursor.fetchone()
    
    current_stats = query_stats(start.timestamp(), end.timestamp())
    previous_stats = query_stats(p_start.timestamp(), p_end.timestamp())
    
    if not current_stats or not current_stats[0]:
        await bot.send_message(chat_id=user_id, text=_(user_id, no_act_key), parse_mode='Markdown')
        conn.close()
        return

    c_count, c_dist, c_time, c_elev, c_tss = current_stats
    p_count, p_dist, p_time, p_elev, p_tss = previous_stats if previous_stats else (0, 0, 0, 0, 0)
    
    def format_comparison(current, previous):
        if previous is None or previous == 0: return ""
        current, previous = current or 0, previous or 0
        diff = ((current - previous) / previous) * 100
        return f" `({'+' if diff >= 0 else ''}{diff:.0f}%)`"
    
    message = [
        _(user_id, title_key),
        _(user_id, "report_rides").format(count=c_count, comparison=format_comparison(c_count, p_count)),
        _(user_id, "report_dist").format(dist=(c_dist or 0), comparison=format_comparison(c_dist, p_dist)),
        _(user_id, "report_time").format(time=format_duration(c_time or 0), comparison=format_comparison(c_time, p_time)),
        _(user_id, "report_elev").format(elev=(c_elev or 0), comparison=format_comparison(c_elev, p_elev)),
        f"🎯 **TSS**: {c_tss or 0:.1f}{format_comparison(c_tss, p_tss)}"
    ]
    
    # 添加专业分析反馈
    if report_type == 'weekly' and (c_tss or 0) > 0:
        message.append(f"\n{get_tss_feedback(c_tss)}")
    
    # 只有周报生成趋势图，月报年报数据点太多可能不直观
    trend_path = None
    if report_type == 'weekly':
        cursor.execute("""
            SELECT date(start_date, 'unixepoch', 'localtime') as day, SUM(suffer_score) 
            FROM activities 
            WHERE telegram_user_id = ? AND start_date >= ? AND start_date < ?
            GROUP BY day ORDER BY day ASC
        """, (user_id, start.timestamp(), end.timestamp()))
        trend_data = cursor.fetchall()
        if trend_data:
            dates = [row[0][5:] for row in trend_data]
            scores = [row[1] or 0 for row in trend_data]
            trend_path = await generate_suffer_trend(user_id, dates, scores)

    conn.close()
    
    final_text = "\n".join(message)
    try:
        if trend_path:
            await bot.send_photo(photo=open(trend_path, 'rb'), caption=final_text, parse_mode='Markdown')
        else:
            await bot.send_message(chat_id=user_id, text=final_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"发送报表给用户 {user_id} 失败: {e}")

async def send_periodic_reports(application: Application):
    """
    发送定期的个人报表任务 (由 Scheduler 调用)
    """
    now = datetime.now(timezone.utc)
    # 根据当前日期判断是哪种推送
    report_type = None
    if now.month == 1 and now.day == 1:
        report_type = 'yearly'
    elif now.day == 1:
        report_type = 'monthly'
    elif now.weekday() == 0: # Monday
        report_type = 'weekly'
    
    if not report_type:
        return

    logger.info(f"触发定时任务：开始推送 {report_type} 报表...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_user_id FROM users WHERE strava_access_token IS NOT NULL")
    users = cursor.fetchall()
    conn.close()
    
    for (user_id,) in users:
        await generate_and_send_user_report(user_id, application.bot, report_type)

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

async def check_weather_alerts(context: ContextTypes.DEFAULT_TYPE):
    """检查明天是否有计划周期性骑行，并提供天气预警"""
    logger.info("开始检查天气预警...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_user_id, riding_schedule FROM users WHERE riding_schedule IS NOT NULL")
    users = cursor.fetchall()
    
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime('%a').lower()
    
    # 获取默认城市 (如果用户没设，这里暂用北京作为示例，实际应结合地理位置)
    for user_id, schedule_str in users:
        schedule = json.loads(schedule_str)
        if tomorrow in schedule:
            plan_time = schedule[tomorrow]
            msg = f"🔔 **骑行提醒**\n\n你计划明天 ({tomorrow.upper()}) {plan_time} 骑行。\n\n预祝你一路顺风！以下是示例城市 (Beijing) 的天气预报："
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode='Markdown')
            # 调用已有的天气发送函数
            await get_weather_for_city(user_id, "Beijing", context, user_id)
    conn.close()

async def check_goal_progress(context: ContextTypes.DEFAULT_TYPE):
    """检查月度目标进度并提醒"""
    logger.info("开始检查目标进度...")
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0).timestamp()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_user_id, monthly_goal_dist FROM users WHERE monthly_goal_dist > 0")
    users = cursor.fetchall()
    
    for user_id, goal in users:
        cursor.execute("SELECT SUM(distance) FROM activities WHERE telegram_user_id = ? AND start_date >= ?", (user_id, month_start))
        current_dist = cursor.fetchone()[0] or 0
        
        progress = (current_dist / goal) * 100
        days_in_month = (now.replace(month=now.month % 12 + 1, day=1) - timedelta(days=1)).day
        expected_progress = (now.day / days_in_month) * 100
        
        if progress < expected_progress - 10: # 落后 10% 以上
            msg = f"📈 **目标进度提醒**\n\n本月目标：{goal} km\n当前已完成：{current_dist:.1f} km ({progress:.1f}%)\n\n目前本月已过去 {now.day} 天，进度略微落后。保持节奏，加油骑手！🚴‍♂️"
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode='Markdown')
    conn.close()
