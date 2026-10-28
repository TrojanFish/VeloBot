import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.locales import t
from src.utils import get_specs
from src.database import (
    get_user_lang, set_user_lang,
    add_kit_waiter, record_maintenance_done, get_user_maintenance
)

logger = logging.getLogger(__name__)

async def handle_lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理語言切換"""
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user

    if data == "lang_select_menu":
        lang = get_user_lang(user.id, user.language_code)
        keyboard = [
            [
                InlineKeyboardButton("🇹🇼 繁體中文", callback_data="lang_set_zh_hant"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_set_en")
            ],
            [
                InlineKeyboardButton(t("btn_back_menu", lang=lang), callback_data="main_menu_refresh")
            ]
        ]
        await query.edit_message_text(
            t("lang_switch_prompt", lang=lang),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data in ("lang_set_zh_hant", "lang_set_en"):
        new_lang = "zh_hant" if data == "lang_set_zh_hant" else "en"
        set_user_lang(user.id, new_lang)
        confirm_text = t("lang_switched", lang=new_lang)

        # 刷新主選單
        keyboard = [
            [
                InlineKeyboardButton(t("btn_torque", lang=new_lang), callback_data="torque_menu"),
                InlineKeyboardButton(t("btn_bb", lang=new_lang), callback_data="bb_menu")
            ],
            [
                InlineKeyboardButton(t("btn_calc", lang=new_lang), callback_data="calc_menu"),
                InlineKeyboardButton(t("btn_mybike", lang=new_lang), callback_data="maint_view")
            ],
            [
                InlineKeyboardButton(t("btn_ask", lang=new_lang), callback_data="entry_ask_noise"),
                InlineKeyboardButton(t("btn_lang", lang=new_lang), callback_data="lang_select_menu")
            ]
        ]
        welcome_text = t("welcome", lang=new_lang, name=user.first_name)
        await query.edit_message_text(
            f"{confirm_text}\n\n{welcome_text}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_main_menu_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """返回並刷新主選單"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = get_user_lang(user.id, user.language_code)

    keyboard = [
        [
            InlineKeyboardButton(t("btn_torque", lang=lang), callback_data="torque_menu"),
            InlineKeyboardButton(t("btn_bb", lang=lang), callback_data="bb_menu")
        ],
        [
            InlineKeyboardButton(t("btn_calc", lang=lang), callback_data="calc_menu"),
            InlineKeyboardButton(t("btn_mybike", lang=lang), callback_data="maint_view")
        ],
        [
            InlineKeyboardButton(t("btn_ask", lang=lang), callback_data="entry_ask_noise"),
            InlineKeyboardButton(t("btn_lang", lang=lang), callback_data="lang_select_menu")
        ]
    ]
    await query.edit_message_text(
        t("welcome", lang=lang, name=user.first_name),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_torque_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理扭力查詢內聯按鈕"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = get_user_lang(user.id, user.language_code)
    specs = get_specs(lang).get("torque", {})
    data = query.data

    if data == "torque_menu":
        keyboard = [
            [
                InlineKeyboardButton(specs.get("cockpit", {}).get("name", "🚲 龍頭車把座管"), callback_data="torque_cat_cockpit"),
                InlineKeyboardButton(specs.get("drivetrain", {}).get("name", "⚙️ 大盤曲柄踏板"), callback_data="torque_cat_drivetrain")
            ],
            [
                InlineKeyboardButton(specs.get("brakes_wheels", {}).get("name", "💿 碟煞飛輪輪組"), callback_data="torque_cat_brakes_wheels"),
                InlineKeyboardButton(specs.get("derailleurs", {}).get("name", "🔄 變速器與勾爪"), callback_data="torque_cat_derailleurs")
            ],
            [
                InlineKeyboardButton(t("btn_back_menu", lang=lang), callback_data="main_menu_refresh")
            ]
        ]
        await query.edit_message_text(
            t("torque_title", lang=lang),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("torque_cat_"):
        cat_key = data.replace("torque_cat_", "")
        cat_data = specs.get(cat_key)
        if not cat_data:
            await query.edit_message_text("No data found / 未找到數據")
            return

        text = f"🔧 **{cat_data.get('name')}**\n\n"
        for item in cat_data.get("items", []):
            text += f"{item}\n\n"
        text += t("torque_warning", lang=lang)

        keyboard = [[InlineKeyboardButton(t("btn_back_list", lang=lang), callback_data="torque_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_bb_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理五通匹配器按鈕"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = get_user_lang(user.id, user.language_code)
    specs = get_specs(lang).get("bb_matcher", {})
    data = query.data

    if data == "bb_menu":
        if lang == "en":
            frames = [
                ("BSA Threaded (68mm)", "bb_frame_BSA"),
                ("BB86 PressFit (41mm ID)", "bb_frame_BB86"),
                ("T47 Internal (85.5/86.5mm)", "bb_frame_T47_IN"),
                ("PF30 PressFit (46mm ID)", "bb_frame_PF30")
            ]
        else:
            frames = [
                ("BSA 英規螺紋 (68mm)", "bb_frame_BSA"),
                ("BB86 壓入式 (41mm內徑)", "bb_frame_BB86"),
                ("T47 內藏式 (85.5/86.5mm)", "bb_frame_T47_IN"),
                ("PF30 壓入式 (46mm內徑)", "bb_frame_PF30")
            ]
        keyboard = [[InlineKeyboardButton(name, callback_data=cb)] for name, cb in frames]
        keyboard.append([InlineKeyboardButton(t("btn_back_menu", lang=lang), callback_data="main_menu_refresh")])

        await query.edit_message_text(
            t("bb_title", lang=lang),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("bb_frame_"):
        frame_key = data.replace("bb_frame_", "")
        frame_data = specs.get(frame_key)
        if not frame_data:
            await query.edit_message_text("No data found")
            return

        keyboard = [
            [InlineKeyboardButton("Shimano 24mm (R7100 / R8100 / R9200)", callback_data=f"bb_match_{frame_key}_SHIMANO_24")],
            [InlineKeyboardButton("SRAM DUB 28.99mm (Rival / Force / Red AXS)", callback_data=f"bb_match_{frame_key}_SRAM_DUB")],
            [InlineKeyboardButton("30mm Spindle (Rotor / Easton)", callback_data=f"bb_match_{frame_key}_ROTOR_30")],
            [InlineKeyboardButton(t("btn_back_list", lang=lang), callback_data="bb_menu")]
        ]

        await query.edit_message_text(
            t("bb_step2", lang=lang, frame=frame_data.get("name")),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("bb_match_"):
        parts = data.split("_")
        frame_key = parts[2]
        spindle_key = "_".join(parts[3:])

        frame_data = specs.get(frame_key, {})
        match_info = frame_data.get(spindle_key)

        if not match_info:
            text = t("bb_no_match", lang=lang)
        else:
            text = t("bb_result_title", lang=lang, content=match_info)

        keyboard = [
            [InlineKeyboardButton("🔄 " + ("Other Spindle" if lang == "en" else "查詢其他軸心"), callback_data=f"bb_frame_{frame_key}")],
            [InlineKeyboardButton(t("btn_back_list", lang=lang), callback_data="bb_menu")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_calc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理計算器點選"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = get_user_lang(user.id, user.language_code)
    specs = get_specs(lang).get("calculator", {})
    data = query.data

    if data == "calc_menu":
        keyboard = [
            [InlineKeyboardButton(t("calc_btn_chain", lang=lang), callback_data="calc_chain")],
            [InlineKeyboardButton(t("calc_btn_tubeless", lang=lang), callback_data="calc_tubeless")],
            [InlineKeyboardButton(t("btn_back_menu", lang=lang), callback_data="main_menu_refresh")]
        ]
        await query.edit_message_text(
            t("calc_title", lang=lang),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data == "calc_chain":
        chain_info = specs.get("chain_formula", {})
        if lang == "en":
            text = (
                f"📏 **{chain_info.get('name')}**\n\n"
                f"📐 **Formula**:\n`{chain_info.get('formula')}`\n\n"
                f"📝 **Parameters**:\n{chain_info.get('note')}\n\n"
                f"💡 **Direct Command**:\nType `/chain <big> <max_cog> <chainstay_mm>`\n"
                f"Example: `/chain 50 34 410`"
            )
        else:
            text = (
                f"📏 **{chain_info.get('name')}**\n\n"
                f"📐 **標準計算公式**：\n`{chain_info.get('formula')}`\n\n"
                f"📝 **參數說明**：\n{chain_info.get('note')}\n\n"
                f"💡 **快捷指令估算**：\n直接在輸入框發送：\n`/chain <大盤齒數> <最大飛輪齒數> <後下叉長度mm>`\n"
                f"例如：`/chain 50 34 410`"
            )
        keyboard = [[InlineKeyboardButton(t("btn_back_list", lang=lang), callback_data="calc_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "calc_tubeless":
        tl_info = specs.get("tubeless_sealant", {})
        title = "🥛 **Tubeless Sealant Guide**\n\n" if lang == "en" else "🥛 **公路車無內胎補胎液注入量指南**\n\n"
        text = title
        for w in ["25c", "28c", "30c", "32c"]:
            text += f"• **{w}**：{tl_info.get(w, '')}\n"
        tip_header = "\n💡 *Tip*: " if lang == "en" else "\n💡 *技師避坑提示*：\n"
        text += f"{tip_header}{tl_info.get('note', '')}"

        keyboard = [[InlineKeyboardButton(t("btn_back_list", lang=lang), callback_data="calc_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

async def handle_waitlist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """車友預約物料更新"""
    query = update.callback_query
    data = query.data
    video_id = data.replace("waitlist_add_", "")
    user = query.from_user
    lang = get_user_lang(user.id, user.language_code)

    add_kit_waiter(video_id, user.id)
    await query.answer(t("waitlist_success", lang=lang), show_alert=True)

async def handle_maintenance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """車友完成保養打卡重置"""
    query = update.callback_query
    data = query.data
    item_type = data.replace("maint_done_", "")
    user = query.from_user
    lang = get_user_lang(user.id, user.language_code)

    presets = get_specs(lang).get("maintenance_presets", {})
    item_cfg = presets.get(item_type)
    if not item_cfg:
        await query.answer("Unknown item")
        return

    cycle_days = item_cfg.get("cycle_days", 90)
    record_maintenance_done(user.id, item_type, cycle_days)

    alert_msg = t("mybike_done_alert", lang=lang, label=item_cfg["label"], cycle=cycle_days)
    await query.answer(alert_msg, show_alert=True)

    # 重新渲染選單
    user_logs = {log["item_type"]: log for log in get_user_maintenance(user.id)}
    text = t("mybike_title", lang=lang)
    keyboard = []
    for k, v in presets.items():
        log = user_logs.get(k)
        if log:
            text += t("mybike_log_item", lang=lang, label=v["label"], last_date=log["last_done_date"], next_date=log["next_remind_date"])
        else:
            text += t("mybike_unrecorded", lang=lang, label=v["label"], cycle=v["cycle_days"])
        keyboard.append([InlineKeyboardButton(t("mybike_btn_done", lang=lang, label=v["label"]), callback_data=f"maint_done_{k}")])
    keyboard.append([InlineKeyboardButton(t("btn_back_menu", lang=lang), callback_data="main_menu_refresh")])

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
