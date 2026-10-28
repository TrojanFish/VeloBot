import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# --- Telegram 机器人配置 ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID") or os.getenv("TELEGRAM_CHAT_ID")
GROUP_ID = os.getenv("GROUP_ID")
ADMIN_ID = os.getenv("ADMIN_ID")
if ADMIN_ID and ADMIN_ID.isdigit():
    ADMIN_ID = int(ADMIN_ID)

# --- YouTube 配置 ---
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "")
YOUTUBE_RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "10"))

# --- 数据目录与文件路径 ---
DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_FILE = os.path.join(DATA_DIR, "bot_data.db")
SPECS_FILE = os.path.join(DATA_DIR, "specs_dict.json")
PAIN_FILE = os.path.join(DATA_DIR, "pain_dict.json")
UPGRADE_FILE = os.path.join(DATA_DIR, "upgrade_dict.json")
