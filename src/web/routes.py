import sqlite3
import logging
from datetime import datetime, timezone
from flask import Flask, request
from src.config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, DB_FILE
from src.utils import _
from stravalib.client import Client
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

flask_app = Flask(__name__)
telegram_app_for_flask = None

async def send_auth_success_message(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    chat_id, athlete_name = job_data['chat_id'], job_data['athlete_name']
    message = _(chat_id, "strava_auth_success").format(athlete_name=athlete_name)
    await context.bot.send_message(chat_id=chat_id, text=message)

@flask_app.route('/strava_auth')
def strava_auth_callback():
    code, state = request.args.get('code'), request.args.get('state')
    if not code or not state: return "授权失败，缺少必要参数。", 400
    telegram_user_id = int(state)
    client = Client()
    try:
        token_response = client.exchange_code_for_token(client_id=STRAVA_CLIENT_ID, client_secret=STRAVA_CLIENT_SECRET, code=code)
        access_token, refresh_token, expires_at = token_response['access_token'], token_response['refresh_token'], token_response['expires_at']
        client.access_token = access_token
        athlete = client.get_athlete()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (telegram_user_id, strava_athlete_id, strava_firstname, strava_lastname, strava_access_token, strava_refresh_token, strava_token_expires_at, strava_last_activity_ts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(telegram_user_id) DO UPDATE SET
            strava_athlete_id=excluded.strava_athlete_id, strava_firstname=excluded.strava_firstname, strava_lastname=excluded.strava_lastname,
            strava_access_token=excluded.strava_access_token, strava_refresh_token=excluded.strava_refresh_token, strava_token_expires_at=excluded.strava_token_expires_at
        ''', (telegram_user_id, athlete.id, athlete.firstname, athlete.lastname, access_token, refresh_token, expires_at, int(datetime.now(timezone.utc).timestamp())))
        conn.commit()
        conn.close()
        logger.info(f"用户 {telegram_user_id} ({athlete.firstname} {athlete.lastname}) 的 Strava 账户已成功关联。")
        
        if telegram_app_for_flask:
            telegram_app_for_flask.job_queue.run_once(send_auth_success_message, 0, data={'chat_id': telegram_user_id, 'athlete_name': athlete.firstname}, name=f"auth_success_{telegram_user_id}")
            
        return "授权成功！现在可以关闭此页面了。", 200
    except Exception as e:
        logger.error(f"Strava token交换失败: {e}")
        return "授权失败，服务器内部错误。", 500

def run_flask_app():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    flask_app.run(host='0.0.0.0', port=5000)
