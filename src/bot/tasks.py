import os
import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.config import ADMIN_ID, DB_FILE
from src.locales import t
from src.utils import get_specs
from src.database import get_user_lang, get_due_maintenance, mark_maintenance_notified
from src.services.youtube import check_youtube_videos

logger = logging.getLogger(__name__)

async def check_youtube_task(context: ContextTypes.DEFAULT_TYPE):
    """YouTube 定時輪詢任務"""
    await check_youtube_videos(context)

async def send_maintenance_reminders(context: ContextTypes.DEFAULT_TYPE):
    """
    每日定時保養提醒任務（每天早上 09:00 執行）
    檢測到期的無內胎補胎液、鏈條浸蠟、煞車油換油記錄並推播私信
    """
    logger.info("開始掃描到期的保養打卡記錄...")
    due_logs = get_due_maintenance()
    if not due_logs:
        logger.info("今日無到期的保養提醒。")
        return

    for log in due_logs:
        user_id = log["user_id"]
        item_type = log["item_type"]
        lang = get_user_lang(user_id)
        presets = get_specs(lang).get("maintenance_presets", {})
        item_info = presets.get(item_type, {"label": item_type, "desc": ""})

        text = t(
            "mybike_reminder_text",
            lang=lang,
            label=item_info["label"],
            last_date=log["last_done_date"],
            desc=item_info.get("desc", "")
        )
        keyboard = [
            [InlineKeyboardButton(t("mybike_reminder_btn", lang=lang), callback_data=f"maint_done_{item_type}")]
        ]

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            mark_maintenance_notified(user_id, item_type)
            logger.info(f"已向車友 {user_id} 發送 {item_type} 保養到期提醒 (語言: {lang})。")
        except Exception as e:
            logger.warning(f"向車友 {user_id} 發送保養提醒失敗: {e}")

async def backup_database_to_admin(context: ContextTypes.DEFAULT_TYPE):
    """
    資料庫異地容災備份（每日凌晨 03:30 執行）
    自動將 SQLite 資料庫檔案作為文檔發送給台長私信
    """
    if not ADMIN_ID:
        return

    if not os.path.exists(DB_FILE):
        logger.warning(f"資料庫備份失敗：未找到檔案 {DB_FILE}")
        return

    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        with open(DB_FILE, "rb") as f:
            await context.bot.send_document(
                chat_id=ADMIN_ID,
                document=f,
                filename=f"velobot_backup_{today_str}.db",
                caption=f"📦 **VeloBot SQLite 資料庫異地容災備份** ({today_str})"
            )
        logger.info("資料庫備份已成功發送給台長。")
    except Exception as e:
        logger.error(f"發送資料庫備份失敗: {e}")
