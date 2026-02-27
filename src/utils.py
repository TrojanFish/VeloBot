import sqlite3
import logging
from src.config import DB_FILE
from src.locales import LOCALIZATION, LOCALIZED_ACHIEVEMENTS

logger = logging.getLogger(__name__)

def get_user_config(user_id: int) -> dict:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (telegram_user_id) VALUES (?)", (user_id,))
    conn.commit()
    cursor.execute("SELECT language, units FROM users WHERE telegram_user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return {
        'lang': result[0] if result and result[0] else 'en',
        'units': result[1] if result and result[1] else 'metric'
    }

def get_user_lang(user_id: int) -> str:
    return get_user_config(user_id)['lang']

def get_user_units(user_id: int) -> str:
    return get_user_config(user_id)['units']

def _(user_id: int, key: str) -> str:
    lang = get_user_lang(user_id)
    return LOCALIZATION.get(lang, LOCALIZATION['en']).get(key, key)

def get_achievement_text(user_id: int, achievement_id: str) -> dict:
    lang = get_user_lang(user_id)
    return LOCALIZED_ACHIEVEMENTS.get(lang, LOCALIZED_ACHIEVEMENTS['en']).get(achievement_id)

def format_duration(seconds):
    h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
    return f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s"

def convert_dist(dist_km: float, units: str) -> str:
    if units == 'imperial':
        return f"{dist_km * 0.621371:.2f} mi"
    return f"{dist_km:.2f} km"

def convert_elev(elev_m: float, units: str) -> str:
    if units == 'imperial':
        return f"{elev_m * 3.28084:.0f} ft"
    return f"{elev_m:.0f} m"

def convert_speed(speed_kmh: float, units: str) -> str:
    if units == 'imperial':
        return f"{speed_kmh * 0.621371:.1f} mph"
    return f"{speed_kmh:.1f} km/h"
