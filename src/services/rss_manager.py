import feedparser
import sqlite3
import logging
import asyncio
from datetime import datetime, timezone
from src.database import get_db_connection

logger = logging.getLogger(__name__)

async def check_rss_feeds(application):
    """
    检查所有订阅的 RSS 源并发送更新
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    # 获取所有有订阅的 feed
    cursor.execute("SELECT feed_id, url, title, last_entry_id FROM rss_feeds")
    feeds = cursor.fetchall()
    
    for feed_id, url, title, last_id in feeds:
        try:
            # 获取该 feed 的所有订阅者
            cursor.execute("SELECT chat_id FROM rss_subscriptions WHERE feed_id = ?", (feed_id,))
            subscribers = [row[0] for row in cursor.fetchall()]
            if not subscribers: continue

            feed = await asyncio.to_thread(feedparser.parse, url)
            if not feed.entries: continue
            
            latest_entry = feed.entries[0]
            entry_id = getattr(latest_entry, 'id', latest_entry.link)
            
            if entry_id != last_id:
                # 发现新条目
                feed_title = feed.feed.get('title', title) or "RSS Feed"
                msg = f"📢 **{feed_title}** 更新了！\n\n🎬 **{latest_entry.title}**\n\n🔗 [阅读全文]({latest_entry.link})"
                
                # 发送给所有订阅者
                for chat_id in subscribers:
                    try:
                        await application.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
                    except Exception as send_err:
                        logger.error(f"发送 RSS 给 {chat_id} 失败: {send_err}")
                
                # 更新最后检查的状态
                cursor.execute("UPDATE rss_feeds SET last_entry_id = ?, last_checked = ? WHERE feed_id = ?", 
                               (entry_id, int(datetime.now(timezone.utc).timestamp()), feed_id))
                conn.commit()
        except Exception as e:
            logger.error(f"检查 RSS 源 {url} 失败: {e}")
            
    conn.close()
