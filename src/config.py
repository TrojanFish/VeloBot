import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# --- 机器人核心参数配置 ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL")
MAPBOX_ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")

# AI 教练配置
AI_API_KEY = os.getenv("AI_API_KEY")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
AI_MODEL = os.getenv("AI_MODEL", "gpt-3.5-turbo")

# Strava API 配置
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")

# 机器人运行的服务器地址
BOT_SERVER_URL = os.getenv("BOT_SERVER_URL", "http://localhost:5000")

# YouTube 频道配置
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "UClxfOUDSPpfZmW0UA2H2LaQ")
YOUTUBE_CHANNEL_RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"

# 数据文件路径
DATA_DIR = "data"
DB_FILE = os.path.join(DATA_DIR, "bot_data.db")
LATEST_VIDEO_ID_FILE = os.path.join(DATA_DIR, "latest_video_id.txt")
