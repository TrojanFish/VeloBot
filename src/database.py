import sqlite3
import os
import logging
from datetime import datetime, timezone
from src.config import DB_FILE, DATA_DIR

logger = logging.getLogger(__name__)

def init_db():
    """初始化数据库, 并兼容旧版本, 自动添加新字段和新表"""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # --- users 表 ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_user_id INTEGER PRIMARY KEY, strava_athlete_id INTEGER UNIQUE, strava_access_token TEXT,
            strava_refresh_token TEXT, strava_token_expires_at INTEGER, strava_last_activity_ts INTEGER,
            strava_notification_mode TEXT NOT NULL DEFAULT 'public', strava_firstname TEXT, strava_lastname TEXT,
            language TEXT NOT NULL DEFAULT 'en'
        )
    ''')
    cursor.execute("PRAGMA table_info(users)")
    columns = [c[1] for c in cursor.fetchall()]
    if 'strava_notification_mode' not in columns: cursor.execute("ALTER TABLE users ADD COLUMN strava_notification_mode TEXT NOT NULL DEFAULT 'public'")
    if 'strava_firstname' not in columns: cursor.execute("ALTER TABLE users ADD COLUMN strava_firstname TEXT")
    if 'strava_lastname' not in columns: cursor.execute("ALTER TABLE users ADD COLUMN strava_lastname TEXT")
    if 'language' not in columns: cursor.execute("ALTER TABLE users ADD COLUMN language TEXT NOT NULL DEFAULT 'en'")

    # --- activities 表 ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            activity_id INTEGER PRIMARY KEY, telegram_user_id INTEGER, start_date INTEGER,
            distance REAL, moving_time INTEGER, elevation_gain REAL,
            FOREIGN KEY(telegram_user_id) REFERENCES users(telegram_user_id)
        )
    ''')

    # --- rides 表 ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rides (
            ride_id INTEGER PRIMARY KEY AUTOINCREMENT, creator_user_id INTEGER, group_chat_id INTEGER, message_id INTEGER,
            title TEXT, ride_time INTEGER, route TEXT, description TEXT, status TEXT NOT NULL DEFAULT 'active',
            FOREIGN KEY(creator_user_id) REFERENCES users(telegram_user_id)
        )
    ''')

    # --- ride_participants 表 ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ride_participants (
            ride_id INTEGER, telegram_user_id INTEGER, PRIMARY KEY (ride_id, telegram_user_id),
            FOREIGN KEY(ride_id) REFERENCES rides(ride_id), FOREIGN KEY(telegram_user_id) REFERENCES users(telegram_user_id)
        )
    ''')

    # --- achievements 表 ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            telegram_user_id INTEGER, achievement_id TEXT, unlocked_date INTEGER,
            PRIMARY KEY (telegram_user_id, achievement_id)
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("数据库初始化完成。")

def get_db_connection():
    return sqlite3.connect(DB_FILE)
