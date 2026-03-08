import logging
import sqlite3
import matplotlib.pyplot as plt
import io
import os
from datetime import datetime, timezone
from src.config import DB_FILE

logger = logging.getLogger(__name__)

def calculate_tss(activity, user_ftp, user_max_hr):
    """
    计算 TSS (Training Stress Score)
    优先使用功率数据，如果没有功率则使用心率估算 (hrTSS)
    """
    duration_sec = float(activity.moving_time)
    
    # 1. 如果有功率数据 (且是设备测量的)
    avg_watts = getattr(activity, 'average_watts', None)
    device_watts = getattr(activity, 'device_watts', False)
    weighted_avg_watts = getattr(activity, 'weighted_average_watts', None)
    
    if avg_watts and device_watts and user_ftp:
        # 使用 NP (Normalized Power) 或平均功率
        np = weighted_avg_watts if weighted_avg_watts else avg_watts
        if_score = np / user_ftp
        tss = (duration_sec * np * if_score) / (user_ftp * 36)
        return tss, np, if_score

    # 2. 如果没有功率，使用心率估算 (Simple hrTSS based on TRIMP)
    avg_hr = getattr(activity, 'average_heartrate', None)
    if avg_hr and user_max_hr:
        # 这是一个简化的估算公式
        intensity = avg_hr / user_max_hr
        # hrTSS = (duration_min * intensity * recovery_factor) - 简化版
        # 这里参考 Strava Suffer Score 的比例，通常 Suffer Score 和 TSS 比例在 1:0.8 到 1:1.2 之间
        suffer_score = getattr(activity, 'suffer_score', 0)
        if suffer_score:
            return suffer_score * 1.0, None, intensity
            
    return 0, None, 0

async def generate_zone_chart(user_id, activity_zones):
    """
    生成心率或功率区间分布图
    activity_zones: 结构应符合 Strava API 的 zones 格式
    """
    if not activity_zones:
        return None

    # 寻找心率区间或功率区间
    target_zone = None
    for zone in activity_zones:
        if zone.type in ['heartrate', 'power']:
            target_zone = zone
            break
    
    if not target_zone or not target_zone.distribution_buckets:
        return None

    labels = [f"Z{i+1}" for i in range(len(target_zone.distribution_buckets))]
    # time 转换为分钟
    values = [b.time / 60 for b in target_zone.distribution_buckets]
    
    colors = ['#3498db', '#2ecc71', '#f1c40f', '#e67e22', '#e74c3c', '#c0392b']
    
    plt.figure(figsize=(8, 5))
    plt.bar(labels, values, color=colors[:len(labels)])
    plt.title(f"Zone Distribution ({target_zone.type.capitalize()})")
    plt.ylabel("Minutes")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 这种方式保存到内存，不需要管理临时文件
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    buf.seek(0)
    
    # 为了方便以后发送，我们还是存到一个临时路径
    temp_path = f"data/zone_{user_id}_{datetime.now().timestamp()}.png"
    with open(temp_path, 'wb') as f:
        f.write(buf.read())
    
    return temp_path

def get_tss_feedback(weekly_tss):
    """根据本周总 TSS 提供专业建议"""
    if weekly_tss == 0:
        return ""
    
    if weekly_tss < 150:
        return "🚴‍♂️ 本周训练负荷较低，适合作为恢复周或刚开始恢复训练。"
    elif weekly_tss < 350:
        return "💪 本周训练量适中，体能正在稳定积攒中，请继续保持。"
    elif weekly_tss < 550:
        return "🔥 本周训练强度较大！你已经进入了高效率提升期，注意补充碳水和睡眠。"
    else:
        return "⚠️ 本周训练量极大！TSS 已超标，建议下周进行积极恢复，避免过度疲劳或受伤。"
