import httpx
import logging
from src.config import FEISHU_WEBHOOK_URL

logger = logging.getLogger(__name__)

async def send_feishu_notification(title: str, content: str):
    """
    发送飞书机器人通知 (富文本格式)
    """
    if not FEISHU_WEBHOOK_URL:
        logger.debug("未配置 FEISHU_WEBHOOK_URL，跳过飞书推送。")
        return

    payload = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": [
                        [
                            {
                                "tag": "text",
                                "text": content
                            }
                        ]
                    ]
                }
            }
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(FEISHU_WEBHOOK_URL, json=payload)
            response.raise_for_status()
            logger.info("飞书通知发送成功。")
    except Exception as e:
        logger.error(f"发送飞书通知失败: {e}")
