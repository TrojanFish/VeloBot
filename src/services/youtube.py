import asyncio
import logging
import html
import httpx
import feedparser
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.config import YOUTUBE_RSS_URL, CHANNEL_ID, ADMIN_ID
from src.database import is_video_exists, add_youtube_video

logger = logging.getLogger(__name__)

async def check_youtube_videos(context: ContextTypes.DEFAULT_TYPE):
    """定時檢查 YouTube 頻道更新並觸發增強型推播 (具備防漏推、非同步超時保護與 HTML 實體防禦)"""
    if not YOUTUBE_RSS_URL or "channel_id=" not in YOUTUBE_RSS_URL or YOUTUBE_RSS_URL.endswith("="):
        logger.debug("未配置有效的 YOUTUBE_CHANNEL_ID，跳過檢查。")
        return

    try:
        logger.info("開始檢查 YouTube 頻道更新...")
        
        # 1. 使用 httpx 進行帶 15 秒超時的非同步請求，防止 feedparser 在網絡波動時永久阻塞執行緒
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(YOUTUBE_RSS_URL)
            if resp.status_code != 200:
                logger.warning(f"獲取 YouTube RSS 失敗，HTTP 狀態碼: {resp.status_code}")
                return
            xml_content = resp.text

        feed = await asyncio.to_thread(feedparser.parse, xml_content)
        if not feed.entries:
            logger.info("未能從 YouTube RSS 獲取到影片條目。")
            return

        bot_info = await context.bot.get_me()
        bot_username = bot_info.username

        # 2. 遍歷最近 5 條條目（逆序：由舊到新發布），徹底消除單條盲區漏推問題
        recent_entries = list(reversed(feed.entries[:5]))

        for entry in recent_entries:
            video_id = getattr(entry, 'yt_videoid', None)
            if not video_id:
                link = getattr(entry, 'link', '')
                if 'v=' in link:
                    video_id = link.split('v=')[1].split('&')[0]

            if not video_id:
                continue

            if is_video_exists(video_id):
                continue

            title = getattr(entry, 'title', f"Video {video_id}")
            title_escaped = html.escape(title)
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            logger.info(f"🎉 發現全新影片！標題: {title} (ID: {video_id})")

            # 頻道端廣播按鈕（雙語清晰標註）
            keyboard = [
                [
                    InlineKeyboardButton("🎬 觀看 YouTube 影片 / Watch Video", url=video_url)
                ],
                [
                    InlineKeyboardButton("🔧 本期工具與扭力清單 / Tool & Torque Sheet", url=f"https://t.me/{bot_username}?start=vid_{video_id}")
                ],
                [
                    InlineKeyboardButton("🩺 異音門診投稿 / Noise Clinic", url=f"https://t.me/{bot_username}?start=ask_noise")
                ]
            ]
            # 採用 HTML 安全格式，徹底免疫 Markdown 特殊字元解析崩潰
            channel_text = (
                f"🎬 <b>新片上映 / New Video: {title_escaped}</b>\n\n"
                f"🔗 <b>YouTube</b>: {video_url}\n\n"
                f"👇 點擊下方按鈕獲取本期組裝工具清單、各部位扭力與避坑要點！\n"
                f"👇 Click buttons below for exclusive build tools, torque specs, or troubleshooting!"
            )

            if CHANNEL_ID:
                try:
                    # 優先嘗試以高清大圖形式發送滿版封面 (maxresdefault.jpg)
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                    try:
                        await context.bot.send_photo(
                            chat_id=CHANNEL_ID,
                            photo=thumbnail_url,
                            caption=channel_text,
                            parse_mode="HTML",
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                        logger.info(f"新影片已成功推播至頻道 {CHANNEL_ID}（帶高清滿版封面）")
                    except Exception as img_err:
                        logger.warning(f"發送高清大圖封面失敗 ({img_err})，降級為標準消息加載網頁預覽")
                        await context.bot.send_message(
                            chat_id=CHANNEL_ID,
                            text=channel_text,
                            parse_mode="HTML",
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            disable_web_page_preview=False
                        )
                        logger.info(f"新影片已成功推播至頻道 {CHANNEL_ID}（網頁預覽模式）")
                except Exception as e:
                    logger.error(f"向頻道 {CHANNEL_ID} 推播新影片失敗: {e}")

            # 向台長私聊發送催更錄入提示
            admin_msg_id = None
            if ADMIN_ID:
                try:
                    admin_prompt = (
                        f"📢 <b>已向頻道推播新影片！</b>\n\n"
                        f"📌 <b>影片標題</b>：{title_escaped}\n"
                        f"🆔 <b>影片ID</b>：<code>{video_id}</code>\n\n"
                        f"💡 <b>【台長專屬免後台綁定】</b>\n"
                        f"請直接<b>長按【回覆/Reply】本條消息</b>，貼上本期用到的專用工具型號、鎖緊扭力或組裝避坑要點。\n"
                        f"Bot 將自動完成綁定並立刻推發給點擊預約的車友！"
                    )
                    msg = await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=admin_prompt,
                        parse_mode="HTML"
                    )
                    admin_msg_id = msg.message_id
                    logger.info(f"已向台長 {ADMIN_ID} 發送物料綁定提示 (msg_id: {admin_msg_id})")
                except Exception as e:
                    logger.error(f"向管理員 {ADMIN_ID} 發送綁定私信失敗: {e}")

            add_youtube_video(video_id=video_id, title=title, admin_msg_id=admin_msg_id)

    except Exception as e:
        logger.error(f"檢查 YouTube 更新時發生異常: {e}", exc_info=True)
