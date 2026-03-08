import os
import logging
from openai import OpenAI
from src.config import AI_API_KEY, AI_BASE_URL, AI_MODEL

logger = logging.getLogger(__name__)

def get_ai_client():
    if not AI_API_KEY:
        return None
    return OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)

async def ask_ai_coach(query, user_data=None, activity_data=None):
    """
    向 AI 教练发送咨询
    query: 用户的咨询内容
    user_data: 用户的基础生理数据 (FTP, HR 等)
    activity_data: 关联的活动数据 (单次或近期汇总)
    """
    client = get_ai_client()
    if not client:
        return "⚠️ 未配置 AI API Key。请在 .env 文件中设置以启用 AI 教练功能。"

    system_prompt = (
        "你是一个专业的自行车训练教练和分析官，名字叫 Velo Coach。"
        "你的任务是根据提供的骑行数据（里程、爬升、TSS、平均心率、功率等）为用户提供专业的反馈和建议。"
        "语气应该专业、鼓励、富有洞察力，并适当使用骑行圈的专业术语。"
        "请使用用户提问时使用的语言进行回复 (默认为中文)。"
    )

    context_prompt = ""
    if user_data:
        context_prompt += f"\n用户信息: FTP 为 {user_data.get('ftp')}W, 最大心率为 {user_data.get('max_hr')}bpm。"
    
    if activity_data:
        context_prompt += f"\n活动详情: \n{activity_data}"

    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{context_prompt}\n\n我的问题是: {query}"}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"AI Coach API Error: {e}")
        return "❌ 抱歉，AI 教练暂时无法响应，请稍后再试。"

async def transcribe_voice(voice_file_path):
    """语音识别转文字 (需使用 Whisper 或其它 API)"""
    client = get_ai_client()
    if not client:
        return None
    
    try:
        with open(voice_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
            return transcript.text
    except Exception as e:
        logger.error(f"Transcript Error: {e}")
        return None
