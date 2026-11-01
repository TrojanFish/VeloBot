import sqlite3
import os
import logging
from datetime import datetime, date, timedelta
from src.config import DB_FILE, DATA_DIR

logger = logging.getLogger(__name__)

def get_db_connection():
    """獲取數據庫連接並強制配置 WAL 模式、5秒超時與正常同步，徹底杜絕 database is locked"""
    conn = sqlite3.connect(DB_FILE, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn

def init_db():
    """初始化 VeloBot 2.0 數據庫架構，並自動平滑遷移舊版表結構"""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # 0. 檢查並平滑遷移舊版 users 表 (相容舊版 telegram_user_id 欄位)
    cursor.execute("PRAGMA table_info(users)")
    user_cols = [c[1] for c in cursor.fetchall()]

    if user_cols:
        if 'user_id' not in user_cols and 'telegram_user_id' in user_cols:
            logger.info("檢測到舊版 users 表，正在自動平滑遷移至 VeloBot 2.0 架構...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users_v2 (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT DEFAULT 'zh_hant',
                    created_at TEXT
                )
            ''')
            has_lang = 'language' in user_cols
            if has_lang:
                cursor.execute("INSERT OR IGNORE INTO users_v2 (user_id, language) SELECT telegram_user_id, COALESCE(language, 'zh_hant') FROM users")
            else:
                cursor.execute("INSERT OR IGNORE INTO users_v2 (user_id, language) SELECT telegram_user_id, 'zh_hant' FROM users")
            cursor.execute("DROP TABLE users")
            cursor.execute("ALTER TABLE users_v2 RENAME TO users")
            logger.info("users 表結構遷移升級成功。")
        else:
            if 'language' not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'zh_hant'")
            if 'created_at' not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'zh_hant',
                created_at TEXT
            )
        ''')

    # 1. YouTube 視頻與裝車物料表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS youtube_videos (
            video_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            published_at TEXT,
            kit_content TEXT DEFAULT NULL,
            admin_msg_id INTEGER DEFAULT NULL
        )
    ''')

    # 2. 視頻物料預約等待隊列
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kit_waitlist (
            video_id TEXT,
            user_id INTEGER,
            created_at TEXT,
            PRIMARY KEY (video_id, user_id)
        )
    ''')

    # 3. 車友時間週期維保打卡記錄表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_logs (
            user_id INTEGER,
            item_type TEXT,
            last_done_date TEXT,
            next_remind_date TEXT,
            is_notified INTEGER DEFAULT 0,
            last_notified_date TEXT DEFAULT NULL,
            PRIMARY KEY (user_id, item_type)
        )
    ''')
    # 檢查並補足 last_notified_date 欄位（平滑升級）
    cursor.execute("PRAGMA table_info(maintenance_logs)")
    maint_cols = [c[1] for c in cursor.fetchall()]
    if 'last_notified_date' not in maint_cols:
        cursor.execute("ALTER TABLE maintenance_logs ADD COLUMN last_notified_date TEXT DEFAULT NULL")

    # 4. 異音門診與故障工單表 (僅存 Telegram file_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS noise_tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            part_category TEXT,
            media_file_id TEXT,
            media_type TEXT,
            description TEXT,
            admin_forwarded_msg_id INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    ''')

    # 5. 系統全局動態配置表 (如驗證開關等)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )
    ''')

    # 6. 高頻查詢索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_admin_msg ON youtube_videos(admin_msg_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_admin_msg ON noise_tickets(admin_forwarded_msg_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_maint_remind ON maintenance_logs(next_remind_date, is_notified)")

    conn.commit()
    conn.close()
    logger.info("YoloCycling Bot 數據庫初始化完成。")

# ==================== 用戶偏好操作 ====================

def get_user_lang(user_id: int, tg_lang_code: str = None) -> str:
    """獲取用戶語言設定（繁體中文 zh_hant 或 英文 en）"""
    default_lang = "zh_hant"
    if tg_lang_code:
        code = tg_lang_code.lower()
        if code.startswith("en"):
            default_lang = "en"
        elif any(k in code for k in ["hant", "tw", "hk", "mo", "zh"]):
            default_lang = "zh_hant"

    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT language FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row and row['language']:
                return row['language']

            # 修復：使用 INSERT OR IGNORE 而非 ON CONFLICT DO UPDATE，
            # 避免覆蓋用戶已通過 /lang 手動設定的語言偏好
            conn.execute('''
                INSERT OR IGNORE INTO users (user_id, language, created_at)
                VALUES (?, ?, datetime('now'))
            ''', (user_id, default_lang))
            conn.commit()
    except Exception as e:
        logger.error(f"讀取/寫入用戶語言異常: {e}")

    return default_lang

def set_user_lang(user_id: int, lang: str):
    """設置用戶語言偏好"""
    try:
        with get_db_connection() as conn:
            conn.execute('''
                INSERT INTO users (user_id, language, created_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(user_id) DO UPDATE SET language = excluded.language
            ''', (user_id, lang))
            conn.commit()
    except Exception as e:
        logger.error(f"設置用戶語言異常: {e}")

# ==================== YouTube 業務數據操作 ====================

def is_video_exists(video_id: str) -> bool:
    with get_db_connection() as conn:
        row = conn.execute("SELECT 1 FROM youtube_videos WHERE video_id = ?", (video_id,)).fetchone()
        return row is not None

def add_youtube_video(video_id: str, title: str, admin_msg_id: int = None, kit_content: str = None):
    with get_db_connection() as conn:
        conn.execute('''
            INSERT OR REPLACE INTO youtube_videos (video_id, title, published_at, kit_content, admin_msg_id)
            VALUES (?, ?, datetime('now'), ?, ?)
        ''', (video_id, title, kit_content, admin_msg_id))
        conn.commit()

def update_video_kit(video_id: str, kit_content: str):
    with get_db_connection() as conn:
        conn.execute("UPDATE youtube_videos SET kit_content = ? WHERE video_id = ?", (kit_content, video_id))
        conn.commit()

def get_video_by_admin_msg(admin_msg_id: int):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM youtube_videos WHERE admin_msg_id = ?", (admin_msg_id,)).fetchone()
        return dict(row) if row else None

def get_video_by_id(video_id: str):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM youtube_videos WHERE video_id = ?", (video_id,)).fetchone()
        return dict(row) if row else None

def add_kit_waiter(video_id: str, user_id: int):
    with get_db_connection() as conn:
        conn.execute('''
            INSERT OR IGNORE INTO kit_waitlist (video_id, user_id, created_at)
            VALUES (?, ?, datetime('now'))
        ''', (video_id, user_id))
        conn.commit()

def pop_kit_waiters(video_id: str):
    with get_db_connection() as conn:
        rows = conn.execute("SELECT user_id FROM kit_waitlist WHERE video_id = ?", (video_id,)).fetchall()
        user_ids = [r['user_id'] for r in rows]
        conn.execute("DELETE FROM kit_waitlist WHERE video_id = ?", (video_id,))
        conn.commit()
        return user_ids

# ==================== 個人維保管家數據操作 ====================

def record_maintenance_done(user_id: int, item_type: str, cycle_days: int):
    today = date.today().isoformat()
    next_date = (date.today() + timedelta(days=cycle_days)).isoformat()
    with get_db_connection() as conn:
        conn.execute('''
            INSERT OR REPLACE INTO maintenance_logs (user_id, item_type, last_done_date, next_remind_date, is_notified, last_notified_date)
            VALUES (?, ?, ?, ?, 0, NULL)
        ''', (user_id, item_type, today, next_date))
        conn.commit()

def get_user_maintenance(user_id: int):
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM maintenance_logs WHERE user_id = ?", (user_id,)).fetchall()
        return [dict(r) for r in rows]

def get_due_maintenance():
    today = date.today().isoformat()
    with get_db_connection() as conn:
        # 1. 首次到期且未提醒 (is_notified = 0)
        # 2. 逾期超過 7 天仍未打卡者 (每週催促一次，防止忽視一次後徹底啞火)
        rows = conn.execute('''
            SELECT * FROM maintenance_logs 
            WHERE next_remind_date <= ? AND (
                is_notified = 0 
                OR (last_notified_date IS NOT NULL AND last_notified_date <= date('now', '-7 days'))
            )
        ''', (today,)).fetchall()
        return [dict(r) for r in rows]

def mark_maintenance_notified(user_id: int, item_type: str):
    today = date.today().isoformat()
    with get_db_connection() as conn:
        conn.execute('''
            UPDATE maintenance_logs SET is_notified = 1, last_notified_date = ?
            WHERE user_id = ? AND item_type = ?
        ''', (today, user_id, item_type))
        conn.commit()

# ==================== 異音門診工單操作 ====================

def create_noise_ticket(user_id: int, username: str, part: str, media_file_id: str, media_type: str, desc: str) -> int:
    with get_db_connection() as conn:
        cursor = conn.execute('''
            INSERT INTO noise_tickets (user_id, username, part_category, media_file_id, media_type, description, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
        ''', (user_id, username, part, media_file_id, media_type, desc))
        ticket_id = cursor.lastrowid
        conn.commit()
        return ticket_id

def set_ticket_admin_msg(ticket_id: int, admin_msg_id: int):
    with get_db_connection() as conn:
        conn.execute("UPDATE noise_tickets SET admin_forwarded_msg_id = ? WHERE ticket_id = ?", (admin_msg_id, ticket_id))
        conn.commit()

def get_ticket_by_admin_msg(admin_msg_id: int):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM noise_tickets WHERE admin_forwarded_msg_id = ?", (admin_msg_id,)).fetchone()
        return dict(row) if row else None

def update_ticket_status(ticket_id: int, status: str):
    with get_db_connection() as conn:
        conn.execute("UPDATE noise_tickets SET status = ? WHERE ticket_id = ?", (status, ticket_id))
        conn.commit()

# ==================== 系統動態設定操作 ====================

def get_system_setting(key: str, default: str = None) -> str:
    """獲取系統動態設定"""
    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT value FROM system_settings WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default
    except Exception as e:
        logger.error(f"獲取系統設定 {key} 失敗: {e}")
        return default

def set_system_setting(key: str, value: str):
    """保存或更新系統動態設定"""
    try:
        now_str = datetime.now().isoformat()
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO system_settings (key, value, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
                (key, value, now_str)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"保存系統設定 {key} 失敗: {e}")

# ==================== 安全熱備份導出 ====================

def backup_database_to_file(dest_path: str):
    """使用 SQLite 官方 Online Backup API 導出一致性熱備份快照，防止頁面撕裂與 WAL 丟失"""
    with get_db_connection() as src:
        dest_conn = sqlite3.connect(dest_path)
        try:
            src.backup(dest_conn)
        finally:
            dest_conn.close()
