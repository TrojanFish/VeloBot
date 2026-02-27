import httpx
import logging
import pytz
from datetime import datetime
from src.utils import _

logger = logging.getLogger(__name__)

async def get_weather_for_city(chat_id: int, city: str, context, user_id: int):
    async with httpx.AsyncClient() as client:
        try:
            params = {"name": city, "count": 1, "language": "zh", "format": "json"}
            geo_url = "https://geocoding-api.open-meteo.com/v1/search"
            geo_resp = await client.get(geo_url, params=params)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            if not geo_data.get("results"):
                await context.bot.send_message(chat_id=chat_id, text=_(user_id, "weather_city_not_found").format(city=city))
                return
            result = geo_data['results'][0]
            lat, lon = result['latitude'], result['longitude']
            city_name = result.get('name', city)
            await get_weather_for_location(chat_id, lat, lon, context, city_name=city_name)
        except Exception as e:
            logger.error(f"城市天气查询失败: {e}")
            await context.bot.send_message(chat_id=chat_id, text=_(user_id, "weather_fetching_city_error"))

async def get_weather_for_location(chat_id: int, lat: float, lon: float, context, city_name: str = "当前位置"):
    async with httpx.AsyncClient() as client:
        try:
            weather_url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                           f"&current_weather=true&hourly=temperature_2m,relativehumidity_2m,precipitation_probability,windspeed_10m"
                           f"&timezone=auto")
            weather_resp = await client.get(weather_url)
            weather_resp.raise_for_status()
            data = weather_resp.json()
            current, hourly, timezone_str = data['current_weather'], data['hourly'], data['timezone']
            tz = pytz.timezone(timezone_str)
            
            message = [_(chat_id, "weather_title").format(city_name=city_name)]
            message.append(_(chat_id, "weather_current").format(temp=current['temperature'], windspeed=current['windspeed']))
            message.append(_(chat_id, "weather_forecast"))
            
            now_local = datetime.now(tz)
            count = 0
            for i, time_str in enumerate(hourly['time']):
                dt_aware = datetime.fromisoformat(time_str).astimezone(tz)
                if dt_aware > now_local and dt_aware.hour % 3 == 0 and count < 8:
                    message.append(
                        f"`{dt_aware.strftime('%H:%M')}`: {hourly['temperature_2m'][i]:.0f}°C, "
                        f"💧{hourly['precipitation_probability'][i]}%, 💨{hourly['windspeed_10m'][i]:.1f} km/h"
                    )
                    count += 1
            await context.bot.send_message(chat_id=chat_id, text="\n".join(message), parse_mode='Markdown')
        except Exception as e:
            logger.error(f"处理天气数据时出错: {e}")
            await context.bot.send_message(chat_id=chat_id, text=_(chat_id, "weather_processing_error"))
