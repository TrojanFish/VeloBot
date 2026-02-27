import logging
import threading
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram import BotCommand

from src.config import TELEGRAM_BOT_TOKEN
from src.database import init_db
from src.locales import LOCALIZED_COMMANDS
from src.web.routes import run_flask_app, telegram_app_for_flask
from src.services.youtube import check_youtube_videos
from src.bot.tasks import check_strava_activities
from src.bot.handlers import (
    start, help_command, link_strava, toggle_strava_privacy, 
    get_last_activity, get_last_video, get_report, get_leaderboard,
    my_rides, my_achievements, weather, route, language_command,
    welcome, location_handler
)
from src.bot.callbacks import (
    ride_button_callback, location_button_callback, language_button_callback
)
from src.bot.conversations import (
    create_ride, ride_title, ride_time, ride_route, ride_desc, 
    cancel_creation, RIDE_TITLE, RIDE_TIME, RIDE_ROUTE, RIDE_DESC
)
from telegram.ext import ConversationHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- 日志配置 ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application: Application):
    # 为支持的每种语言设置命令
    for lang_code, commands_dict in LOCALIZED_COMMANDS.items():
        commands = [BotCommand(cmd, desc) for cmd, desc in commands_dict.items()]
        await application.bot.set_my_commands(commands, language_code=lang_code)
    
    logger.info("多语言机器人快捷指令已设置。")
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(check_youtube_videos, 'interval', minutes=10, args=[application])
    scheduler.add_job(check_strava_activities, 'interval', minutes=15, args=[application])
    scheduler.start()
    logger.info("后台调度器已启动。")

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("项目启动失败：未找到 TELEGRAM_BOT_TOKEN。请检查 .env 文件。")
        return

    init_db()
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
    # 共享 application 实例给 Flask 路由使用
    import src.web.routes as web_routes
    web_routes.telegram_app_for_flask = application

    # 注册约伴对话处理器
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('create_ride', create_ride)],
        states={
            RIDE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ride_title)],
            RIDE_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ride_time)],
            RIDE_ROUTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ride_route)],
            RIDE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, ride_desc)],
        },
        fallbacks=[CommandHandler('cancel', cancel_creation)],
    )
    
    # 注册所有处理器
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(ride_button_callback, pattern='^join_ride_|^leave_ride_'))
    application.add_handler(CallbackQueryHandler(location_button_callback, pattern='^loc_'))
    application.add_handler(CallbackQueryHandler(language_button_callback, pattern='^set_lang_'))

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("link_strava", link_strava))
    application.add_handler(CommandHandler("toggle_strava_privacy", toggle_strava_privacy))
    application.add_handler(CommandHandler("get_last_activity", get_last_activity))
    application.add_handler(CommandHandler("get_last_video", get_last_video))
    application.add_handler(CommandHandler("report", get_report))
    application.add_handler(CommandHandler("leaderboard", get_leaderboard))
    application.add_handler(CommandHandler("my_rides", my_rides))
    application.add_handler(CommandHandler("my_achievements", my_achievements))
    application.add_handler(CommandHandler("weather", weather))
    application.add_handler(CommandHandler("route", route))
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    application.add_handler(MessageHandler(filters.LOCATION, location_handler))
    
    # 在后台线程中启动 Flask
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    
    logger.info("Flask Web 服务器已在后台启动。")
    logger.info("机器人启动成功，开始监控...")
    
    application.run_polling()

if __name__ == "__main__":
    main()
