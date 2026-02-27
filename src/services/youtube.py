import os
import logging
import feedparser
import asyncio
from src.config import YOUTUBE_CHANNEL_RSS_URL, LATEST_VIDEO_ID_FILE, TELEGRAM_CHAT_ID
from src.locales import LOCALIZATION
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def check_youtube_videos(context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info("开始检查 YouTube 视频更新...")
        feed = await asyncio.to_thread(feedparser.parse, YOUTUBE_CHANNEL_RSS_URL)
        last_known_id = None
        if os.path.exists(LATEST_VIDEO_ID_FILE):
            with open(LATEST_VIDEO_ID_FILE, 'r') as f: last_known_id = f.read().strip()
        if feed.entries:
            latest_video, latest_video_id = feed.entries[0], feed.entries[0].yt_videoid
            if latest_video_id != last_known_id:
                logger.info(f"发现新视频: {latest_video.title}")
                message = LOCALIZATION['en']['new_video_notification'].format(author=latest_video.author, title=latest_video.title) + f"\n\n{latest_video.link}"
                await context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='Markdown', disable_web_page_preview=False)
                with open(LATEST_VIDEO_ID_FILE, 'w') as f: f.write(latest_video_id)
                logger.info(f"新视频 {latest_video.title} 已成功推送。")
            else: 
                logger.info("YouTube 频道无更新。")
        else: 
            logger.warning("无法从 YouTube RSS 源获取视频条目。")
    except Exception as e: 
        logger.error(f"检查 YouTube 更新时发生错误: {e}")
