import os
import httpx
import logging
import polyline
import matplotlib.pyplot as plt
import numpy as np
from src.config import MAPBOX_ACCESS_TOKEN, DATA_DIR

logger = logging.getLogger(__name__)

# 确保图片缓存目录存在
VISUALS_DIR = os.path.join(DATA_DIR, "visuals")
os.makedirs(VISUALS_DIR, exist_ok=True)

async def generate_static_map(activity_id: int, summary_polyline: str):
    """
    使用 Mapbox Static API 生成路线轨迹图
    """
    if not MAPBOX_ACCESS_TOKEN or not summary_polyline:
        logger.debug("缺失 MAPBOX_ACCESS_TOKEN 或 Polyline，跳过地图生成。")
        return None

    try:
        # 对 polyline 进行 URL 编码处理（Mapbox 接受编码后的字符串，但有些字符需要转义）
        encoded_polyline = f"path-5+f44-0.5({summary_polyline})"
        url = f"https://api.mapbox.com/styles/v1/mapbox/outdoors-v11/static/{encoded_polyline}/auto/600x400@2x?access_token={MAPBOX_ACCESS_TOKEN}"
        
        file_path = os.path.join(VISUALS_DIR, f"map_{activity_id}.png")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(response.content)
                return file_path
            else:
                logger.error(f"Mapbox API 错误: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        logger.error(f"生成静态地图失败: {e}")
        return None

async def generate_elevation_profile(activity_id: int, streams):
    """
    生成海拔剖面图
    streams: 由 client.get_activity_streams 返回的数据流
    """
    if not streams or 'altitude' not in streams or 'distance' not in streams:
        return None

    try:
        altitudes = streams['altitude'].data
        distances = [d / 1000 for d in streams['distance'].data]  # 转为 km

        plt.figure(figsize=(8, 3))
        plt.fill_between(distances, altitudes, color='orange', alpha=0.3)
        plt.plot(distances, altitudes, color='darkorange', linewidth=2)
        
        plt.title('Elevation Profile', fontsize=12)
        plt.xlabel('Distance (km)', fontsize=10)
        plt.ylabel('Altitude (m)', fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.5)
        
        file_path = os.path.join(VISUALS_DIR, f"elev_{activity_id}.png")
        plt.savefig(file_path, bbox_inches='tight', dpi=150)
        plt.close()
        return file_path
    except Exception as e:
        logger.error(f"生成海拔剖面图失败: {e}")
        return None

async def generate_suffer_trend(user_id: int, dates, scores):
    """
    生成 Suffer Score 周走势图
    """
    if not scores: return None
    try:
        plt.figure(figsize=(8, 4))
        plt.bar(dates, scores, color='red', alpha=0.6)
        plt.plot(dates, scores, marker='o', color='darkred', linestyle='-', linewidth=2)
        
        plt.title('Suffer Score Weekly Trend', fontsize=14)
        plt.ylabel('Suffer Score', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        file_path = os.path.join(VISUALS_DIR, f"trend_{user_id}_{int(datetime.now().timestamp())}.png")
        plt.savefig(file_path, bbox_inches='tight', dpi=150)
        plt.close()
        return file_path
    except Exception as e:
        logger.error(f"生成趋势图失败: {e}")
        return None
