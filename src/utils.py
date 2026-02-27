import sqlite3
import logging
from src.config import DB_FILE
from src.locales import LOCALIZATION, LOCALIZED_ACHIEVEMENTS

logger = logging.getLogger(__name__)

def get_user_lang(user_id: int) -> str:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (telegram_user_id) VALUES (?)", (user_id,))
    conn.commit()
    cursor.execute("SELECT language FROM users WHERE telegram_user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result and result[0] else 'en'

def _(user_id: int, key: str) -> str:
    lang = get_user_lang(user_id)
    return LOCALIZATION.get(lang, LOCALIZATION['en']).get(key, key)

def get_achievement_text(user_id: int, achievement_id: str) -> dict:
    lang = get_user_lang(user_id)
    return LOCALIZED_ACHIEVEMENTS.get(lang, LOCALIZED_ACHIEVEMENTS['en']).get(achievement_id)

def format_duration(seconds):
    h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
    return f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s"
