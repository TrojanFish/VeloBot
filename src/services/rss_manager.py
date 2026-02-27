import feedparser
import sqlite3
import logging
import asyncio
from datetime import datetime, timezone
from src.config import DB_FILE

logger = logging.getLogger(__name__)

async def check_rss_feeds(application):
    """
    检查所有订阅的 RSS 源并发送更新
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT feed_id, url, title, last_entry_id, chat_id FROM rss_feeds")
    feeds = cursor.fetchall()
    
    for feed_id, url, title, last_id, chat_id in feeds:
        try:
            feed = await asyncio.to_thread(feedparser.parse, url)
            if not feed.entries: continue
            
            latest_entry = feed.entries[0]
            entry_id = getattr(latest_entry, 'id', latest_entry.link)
            
            if entry_id != last_id:
                # 发现新条目
                msg = f"📢 **{feed.feed.get('title', title)}** 更新了！\n\n🎬 **{latest_entry.title}**\n\n🔗 [阅读全文]({latest_entry.link})"
                # 如果是 Telegram
                await application.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
                
                # 更新状态
                cursor.execute("UPDATE rss_feeds SET last_entry_id = ?, last_checked = ? WHERE feed_id = ?", (entry_id, int(datetime.now(timezone.utc).timestamp()), feed_id))
                conn.commit()
        except Exception as e:
            logger.error(f"检查 RSS 源 {url} 失败: {e}")
            
    conn.close()
