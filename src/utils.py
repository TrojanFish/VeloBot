import os
import json
import logging
from src.config import SPECS_FILE

logger = logging.getLogger(__name__)

_specs_cache = None

def get_specs(lang: str = "zh_hant") -> dict:
    """讀取指定語言版本的參數字典 (支援熱重載)"""
    global _specs_cache
    if not os.path.exists(SPECS_FILE):
        logger.error(f"參數字典檔案不存在: {SPECS_FILE}")
        return {}
    try:
        with open(SPECS_FILE, "r", encoding="utf-8") as f:
            _specs_cache = json.load(f)
            # 支援 zh_hant 與 en 兩大分支
            lang_key = "en" if lang == "en" else "zh_hant"
            return _specs_cache.get(lang_key, _specs_cache.get("zh_hant", {}))
    except Exception as e:
        logger.error(f"讀取參數字典失敗: {e}")
        return (_specs_cache.get(lang) if _specs_cache else {}) or {}

def calculate_chain_length(chainstay_mm: float, big_ring_teeth: int, max_cog_teeth: int) -> int:
    """
    計算公路車雙盤標準鏈條節數（Rigout 公式，偶數節）
    L = 2 * (C / 12.7) + (F / 2) + (R / 2) + 1
    """
    raw_length = 2 * (chainstay_mm / 12.7) + (big_ring_teeth / 2.0) + (max_cog_teeth / 2.0) + 1.0
    rounded = round(raw_length)
    if rounded % 2 != 0:
        rounded += 1
    return int(rounded)
