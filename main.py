import logging
import datetime
import warnings
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from pytz import timezone as ZoneInfo
from telegram import BotCommand
from telegram.warnings import PTBUserWarning
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
)

# 忽略 ConversationHandler 針對 CallbackQueryHandler 的常規提示
warnings.filterwarnings("ignore", category=PTBUserWarning)

from src.config import TELEGRAM_BOT_TOKEN, ADMIN_ID, CHECK_INTERVAL_MINUTES
from src.database import init_db
from src.bot.handlers import (
    start, language_command, torque_command, bb_command, pain_command, calc_command,
    chain_calc_command, mybike_command, help_command, admin_reply_handler
)
from src.bot.callbacks import (
    handle_lang_callback, handle_main_menu_refresh,
    handle_torque_callback, handle_bb_callback, handle_pain_callback, handle_calc_callback,
    handle_waitlist_callback, handle_maintenance_callback
)
from src.bot.conversations import noise_conversation_handler
from src.bot.captcha import new_member_captcha, handle_captcha_callback
from src.bot.tasks import (
    check_youtube_task, send_maintenance_reminders, backup_database_to_admin
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application: Application):
    """機器人啟動初始化：註冊繁體中文與英文選單指令及定時調度任務"""
    # 繁體中文指令集
    zh_commands = [
        BotCommand("torque", "🔧 關鍵部位標準鎖緊扭力速查"),
        BotCommand("bb", "⚙️ 五通規格與大盤軸心相容指南"),
        BotCommand("pain", "🩺 騎行疼痛自查與 Fitting 處方籤"),
        BotCommand("calc", "📐 組裝實用計算器選單"),
        BotCommand("chain", "📏 鏈條標準節數計算"),
        BotCommand("mybike", "🚲 個人車輛週期保養管家"),
        BotCommand("ask", "🩺 異音門診與故障投稿"),
        BotCommand("lang", "🌐 切換語言 / Switch Language"),
        BotCommand("help", "📖 使用說明")
    ]

    # 英文指令集
    en_commands = [
        BotCommand("torque", "🔧 Standard torque values lookup"),
        BotCommand("bb", "⚙️ BB & crank spindle compatibility"),
        BotCommand("pain", "🩺 Cycling pain checker & Bike Fit rx"),
        BotCommand("calc", "📐 Bike build calculators"),
        BotCommand("chain", "📏 Chain link length calculation"),
        BotCommand("mybike", "🚲 Maintenance tracker & alerts"),
        BotCommand("ask", "🩺 Noise clinic & symptom submission"),
        BotCommand("lang", "🌐 Switch Language / 切換語言"),
        BotCommand("help", "📖 Help & documentation")
    ]

    try:
        # 1. 預設選單（預設繁體中文，無語言限制）
        await application.bot.set_my_commands(zh_commands)
        # 2. 中文使用者 (zh)
        await application.bot.set_my_commands(zh_commands, language_code="zh")
        # 3. 英文使用者 (en)
        await application.bot.set_my_commands(en_commands, language_code="en")
        logger.info("雙語快捷指令選單註冊完畢。")
    except Exception as e:
        logger.error(f"快捷指令選單註冊失敗: {e}")

    # 定時任務
    job_queue = application.job_queue
    if job_queue:
        shanghai_tz = ZoneInfo("Asia/Shanghai")

        # 定時輪詢 YouTube
        job_queue.run_repeating(
            check_youtube_task,
            interval=CHECK_INTERVAL_MINUTES * 60,
            first=15
        )
        logger.info(f"YouTube 輪詢任務已加載（每 {CHECK_INTERVAL_MINUTES} 分鐘一次）。")

        # 每日早上 09:00 推播保養提醒
        remind_time = datetime.time(hour=9, minute=0, tzinfo=shanghai_tz)
        job_queue.run_daily(send_maintenance_reminders, time=remind_time)
        logger.info("每日 09:00 保養提醒任務已加載。")

        # 每日凌晨 03:30 自動向台長發送資料庫備份
        backup_time = datetime.time(hour=3, minute=30, tzinfo=shanghai_tz)
        job_queue.run_daily(backup_database_to_admin, time=backup_time)
        logger.info("每日 03:30 資料庫備份任務已加載。")

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("未找到 TELEGRAM_BOT_TOKEN，請檢查 .env 檔案。")
        return

    init_db()

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # 1. 註冊異音門診對話狀態機 (/ask)
    application.add_handler(noise_conversation_handler)

    # 2. 註冊核心指令
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("torque", torque_command))
    application.add_handler(CommandHandler("bb", bb_command))
    application.add_handler(CommandHandler("pain", pain_command))
    application.add_handler(CommandHandler("calc", calc_command))
    application.add_handler(CommandHandler("chain", chain_calc_command))
    application.add_handler(CommandHandler("mybike", mybike_command))
    application.add_handler(CommandHandler("lang", language_command))
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", start))

    # 3. 註冊內聯鍵盤回調
    application.add_handler(CallbackQueryHandler(handle_lang_callback, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(handle_main_menu_refresh, pattern="^main_menu_refresh$"))
    application.add_handler(CallbackQueryHandler(handle_torque_callback, pattern="^torque_"))
    application.add_handler(CallbackQueryHandler(handle_bb_callback, pattern="^bb_"))
    application.add_handler(CallbackQueryHandler(handle_pain_callback, pattern="^pain_"))
    application.add_handler(CallbackQueryHandler(handle_calc_callback, pattern="^calc_"))
    application.add_handler(CallbackQueryHandler(handle_waitlist_callback, pattern="^waitlist_add_"))
    application.add_handler(CallbackQueryHandler(handle_maintenance_callback, pattern="^maint_done_"))
    application.add_handler(CallbackQueryHandler(mybike_command, pattern="^maint_view$"))
    application.add_handler(CallbackQueryHandler(handle_captcha_callback, pattern="^cpt:"))

    # 4. 討論群入群硬核防刷驗證
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_captcha))

    # 5. 台長專屬免後台【回覆/Reply】攔截器
    if ADMIN_ID:
        application.add_handler(
            MessageHandler(
                filters.TEXT & filters.REPLY & filters.User(user_id=ADMIN_ID),
                admin_reply_handler
            )
        )

    # 6. 全域異常處理器
    async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error("處理 Telegram 更新時發生未捕獲異常:", exc_info=context.error)

    application.add_error_handler(global_error_handler)

    logger.info("VeloBot 2.0 雙語版啟動成功，開始 Long Polling 監聽...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
