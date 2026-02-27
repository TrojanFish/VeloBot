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
            strava_notification_mode TEXT NOT NULL DEFAULT 'private', strava_firstname TEXT, strava_lastname TEXT,
            language TEXT NOT NULL DEFAULT 'en', units TEXT NOT NULL DEFAULT 'metric'
        )
    ''')
    cursor.execute("PRAGMA table_info(users)")
    columns = [c[1] for c in cursor.fetchall()]
    if 'strava_notification_mode' not in columns: cursor.execute("ALTER TABLE users ADD COLUMN strava_notification_mode TEXT NOT NULL DEFAULT 'private'")
    if 'strava_firstname' not in columns: cursor.execute("ALTER TABLE users ADD COLUMN strava_firstname TEXT")
    if 'strava_lastname' not in columns: cursor.execute("ALTER TABLE users ADD COLUMN strava_lastname TEXT")
    if 'language' not in columns: cursor.execute("ALTER TABLE users ADD COLUMN language TEXT NOT NULL DEFAULT 'en'")
    if 'units' not in columns: cursor.execute("ALTER TABLE users ADD COLUMN units TEXT NOT NULL DEFAULT 'metric'")

    # --- activities 表 ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            activity_id INTEGER PRIMARY KEY, telegram_user_id INTEGER, start_date INTEGER,
            distance REAL, moving_time INTEGER, elevation_gain REAL,
            suffer_score REAL, avg_hr REAL, gear_id TEXT,
            FOREIGN KEY(telegram_user_id) REFERENCES users(telegram_user_id)
        )
    ''')
    cursor.execute("PRAGMA table_info(activities)")
    act_columns = [c[1] for c in cursor.fetchall()]
    if 'suffer_score' not in act_columns: cursor.execute("ALTER TABLE activities ADD COLUMN suffer_score REAL")
    if 'avg_hr' not in act_columns: cursor.execute("ALTER TABLE activities ADD COLUMN avg_hr REAL")
    if 'gear_id' not in act_columns: cursor.execute("ALTER TABLE activities ADD COLUMN gear_id TEXT")

    # --- gear 表 (追踪自行车/器材) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gear (
            gear_id TEXT PRIMARY KEY, telegram_user_id INTEGER, name TEXT, brand_name TEXT, model_name TEXT,
            distance REAL DEFAULT 0, is_primary INTEGER DEFAULT 0,
            FOREIGN KEY(telegram_user_id) REFERENCES users(telegram_user_id)
        )
    ''')

    # --- maintenance 表 (保养提醒) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT, gear_id TEXT, part_name TEXT, 
            threshold_dist REAL, last_service_dist REAL DEFAULT 0, notified INTEGER DEFAULT 0,
            FOREIGN KEY(gear_id) REFERENCES gear(gear_id)
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

    # --- RSS系统表 ---
    # 存储源信息
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rss_feeds (
            feed_id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQUE, title TEXT,
            last_entry_id TEXT, last_checked INTEGER
        )
    ''')
    # 检查旧版本是否存在 chat_id 字段并迁移
    cursor.execute("PRAGMA table_info(rss_feeds)")
    rss_columns = [c[1] for c in cursor.fetchall()]
    
    # 存储订阅关系 (哪个群订阅了哪个源)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rss_subscriptions (
            feed_id INTEGER, chat_id INTEGER,
            PRIMARY KEY (feed_id, chat_id),
            FOREIGN KEY(feed_id) REFERENCES rss_feeds(feed_id)
        )
    ''')
    
    if 'chat_id' in rss_columns:
        logger.info("发现旧版 RSS 数据，正在迁移订阅关系...")
        cursor.execute("SELECT feed_id, chat_id FROM rss_feeds WHERE chat_id IS NOT NULL")
        old_data = cursor.fetchall()
        for f_id, c_id in old_data:
            cursor.execute("INSERT OR IGNORE INTO rss_subscriptions (feed_id, chat_id) VALUES (?, ?)", (f_id, c_id))
        # 迁移后清理旧表（删除列较复杂，这里选择重命名并重新创建）
        try:
            cursor.execute("ALTER TABLE rss_feeds RENAME TO rss_feeds_old")
            cursor.execute('''
                CREATE TABLE rss_feeds (
                    feed_id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQUE, title TEXT,
                    last_entry_id TEXT, last_checked INTEGER
                )
            ''')
            cursor.execute("INSERT INTO rss_feeds (feed_id, url, title, last_entry_id, last_checked) SELECT feed_id, url, title, last_entry_id, last_checked FROM rss_feeds_old")
            cursor.execute("DROP TABLE rss_feeds_old")
            logger.info("RSS 数据迁移完成。")
        except Exception as e:
            logger.error(f"RSS 数据迁移失败: {e}")

    conn.commit()
    conn.close()
    logger.info("数据库初始化完成。")

def get_db_connection():
    return sqlite3.connect(DB_FILE)
