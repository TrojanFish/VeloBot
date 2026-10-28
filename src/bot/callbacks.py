import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.locales import t
from src.utils import get_specs, get_pain_specs, get_upgrade_specs
from src.services.tire_calc import calculate_tire_pressure, format_tire_pressure_card
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
                InlineKeyboardButton(t("btn_pain", lang=new_lang), callback_data="pain_menu"),
                InlineKeyboardButton(t("btn_roi", lang=new_lang), callback_data="roi_menu")
            ],
            [
                InlineKeyboardButton(t("btn_psi", lang=new_lang), callback_data="psi_menu"),
                InlineKeyboardButton(t("btn_calc", lang=new_lang), callback_data="calc_menu")
            ],
            [
                InlineKeyboardButton(t("btn_mybike", lang=new_lang), callback_data="maint_view"),
                InlineKeyboardButton(t("btn_ask", lang=new_lang), callback_data="entry_ask_noise")
            ],
            [
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
            InlineKeyboardButton(t("btn_pain", lang=lang), callback_data="pain_menu"),
            InlineKeyboardButton(t("btn_roi", lang=lang), callback_data="roi_menu")
        ],
        [
            InlineKeyboardButton(t("btn_psi", lang=lang), callback_data="psi_menu"),
            InlineKeyboardButton(t("btn_calc", lang=lang), callback_data="calc_menu")
        ],
        [
            InlineKeyboardButton(t("btn_mybike", lang=lang), callback_data="maint_view"),
            InlineKeyboardButton(t("btn_ask", lang=lang), callback_data="entry_ask_noise")
        ],
        [
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

async def handle_pain_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理騎行疼痛自查與 Bike Fitting 處方籤按鈕點選"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = get_user_lang(user.id, user.language_code)
    pain_data = get_pain_specs(lang)
    data = query.data

    # 主選單：部位選擇
    if data == "pain_menu":
        areas = pain_data.get("areas", {})
        keyboard = []
        area_keys = list(areas.keys())
        for i in range(0, len(area_keys), 2):
            row = [InlineKeyboardButton(areas[area_keys[i]]["title"], callback_data=f"pain_area_{area_keys[i]}")]
            if i + 1 < len(area_keys):
                row.append(InlineKeyboardButton(areas[area_keys[i+1]]["title"], callback_data=f"pain_area_{area_keys[i+1]}"))
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton(t("btn_back_menu", lang=lang), callback_data="main_menu_refresh")])

        await query.edit_message_text(
            t("pain_intro", lang=lang),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # 第 2 步：情境/時機選擇
    if data.startswith("pain_area_"):
        area_id = data.replace("pain_area_", "")
        areas = pain_data.get("areas", {})
        timings = pain_data.get("timings", {})
        area_info = areas.get(area_id, {})
        area_title = area_info.get("title", area_id)

        keyboard = []
        for timing_id, timing_info in timings.items():
            keyboard.append([InlineKeyboardButton(timing_info["title"], callback_data=f"pain_rx_{area_id}_{timing_id}")])
        keyboard.append([InlineKeyboardButton(t("btn_back_list", lang=lang), callback_data="pain_menu")])

        await query.edit_message_text(
            t("pain_step2", lang=lang, area=area_title),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # 第 3 步：生成處方籤卡片
    if data.startswith("pain_rx_"):
        parts = data.split("_")
        # pain_rx_<area_id>_<timing_id>
        area_id = parts[2]
        timing_id = "_".join(parts[3:])

        areas = pain_data.get("areas", {})
        timings = pain_data.get("timings", {})
        prescriptions = pain_data.get("prescriptions", {})

        area_title = areas.get(area_id, {}).get("title", area_id)
        timing_info = timings.get(timing_id, {})
        timing_title = timing_info.get("title", timing_id)

        rx = prescriptions.get(area_id, {}).get(timing_id, {})
        if not rx:
            await query.edit_message_text("No prescription found / 暫無該情境的處方數據")
            return

        if lang == "en":
            text = (
                f"🩺 **Bike Fitting Prescription Card**\n\n"
                f"🎯 **Target Area**: {area_title}\n"
                f"⏱️ **Scenario**: {timing_title}\n\n"
                f"📋 **Diagnosis**: {rx.get('diagnosis')}\n\n"
                f"🔬 **Biomechanism**: {rx.get('mechanism')}\n\n"
                f"⚙️ **Mechanical Adjustments**:\n"
            )
            for m in rx.get("mechanical", []):
                text += f"• {m}\n"
            text += f"\n🚴 **Riding Technique Fixes**:\n"
            for r in rx.get("riding", []):
                text += f"• {r}\n"
            text += f"\n🧘 **Targeted Stretches & Exercises**:\n"
            for s in rx.get("stretches", []):
                text += f"• {s}\n"
        else:
            text = (
                f"🩺 **公路車騎行疼痛與 Fitting 調校處方籤**\n\n"
                f"🎯 **疼痛部位**：{area_title}\n"
                f"⏱️ **誘發情境**：{timing_title}\n\n"
                f"📋 **病因診斷**：{rx.get('diagnosis')}\n\n"
                f"🔬 **受力機理**：{rx.get('mechanism')}\n\n"
                f"⚙️ **車輛設定調整建議**：\n"
            )
            for m in rx.get("mechanical", []):
                text += f"• {m}\n"
            text += f"\n🚴 **騎乘姿勢與發力修正**：\n"
            for r in rx.get("riding", []):
                text += f"• {r}\n"
            text += f"\n🧘 **專案拉伸與康復動作**：\n"
            for s in rx.get("stretches", []):
                text += f"• {s}\n"

        keyboard = [
            [InlineKeyboardButton("🔄 " + ("Other Scenarios" if lang == "en" else "查詢其他時機"), callback_data=f"pain_area_{area_id}")],
            [InlineKeyboardButton(t("pain_btn_restart", lang=lang), callback_data="pain_menu")],
            [InlineKeyboardButton(t("pain_btn_ask", lang=lang), callback_data="entry_ask_noise")],
            [InlineKeyboardButton(t("btn_back_menu", lang=lang), callback_data="main_menu_refresh")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_roi_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理改裝升級省瓦 ROI 內聯回調"""
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    lang = get_user_lang(user.id, user.language_code)
    specs = get_upgrade_specs(lang)
    categories = specs.get("categories", {})
    items = specs.get("items", [])

    # 1. 頂層分類選單 (roi_menu)
    if data == "roi_menu":
        keyboard = []
        cat_keys = list(categories.keys())
        for i in range(0, len(cat_keys), 2):
            row = [InlineKeyboardButton(categories[cat_keys[i]][lang if lang in categories[cat_keys[i]] else "zh_hant"], callback_data=f"roi_cat_{cat_keys[i]}")]
            if i + 1 < len(cat_keys):
                row.append(InlineKeyboardButton(categories[cat_keys[i+1]][lang if lang in categories[cat_keys[i+1]] else "zh_hant"], callback_data=f"roi_cat_{cat_keys[i+1]}"))
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton(t("btn_back_menu", lang=lang), callback_data="main_menu_refresh")])

        await query.edit_message_text(
            t("roi_intro", lang=lang),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # 2. 分類內各升級品項列表 (roi_cat_<cat_id>)
    if data.startswith("roi_cat_"):
        cat_id = data.replace("roi_cat_", "")
        cat_title = categories.get(cat_id, {}).get(lang if lang in categories.get(cat_id, {}) else "zh_hant", cat_id)

        cat_items = [it for it in items if it.get("category") == cat_id]
        keyboard = []
        for it in cat_items:
            name_str = it["name"].get(lang, it["name"].get("zh_hant", it["id"]))
            keyboard.append([InlineKeyboardButton(name_str, callback_data=f"roi_item_{it['id']}")])
        keyboard.append([InlineKeyboardButton(t("roi_btn_back", lang=lang), callback_data="roi_menu")])
        keyboard.append([InlineKeyboardButton(t("btn_back_menu", lang=lang), callback_data="main_menu_refresh")])

        prompt = f"🚀 **{cat_title}**\n\n" + ("Select an item to view data & ROI analysis:" if lang == "en" else "請點選具體升級品項查看風洞省瓦數據與性價比分析：")
        await query.edit_message_text(prompt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # 3. 升級品項詳情卡片 (roi_item_<item_id>)
    if data.startswith("roi_item_"):
        item_id = data.replace("roi_item_", "")
        item = next((it for it in items if it.get("id") == item_id), None)
        if not item:
            await query.edit_message_text("Item not found / 找不到對應升級品項")
            return

        cat_id = item.get("category", "aero")
        if lang == "en":
            wt_g = item['weight_save_g']
            wt_str = f"Saves {wt_g}g" if wt_g > 0 else (f"+{abs(wt_g)}g" if wt_g < 0 else "0g")
            text = (
                f"🚀 <b>{item['name'].get('en', item['id'])}</b>\n"
                f"───────────────────\n"
                f"⚡ <b>40 km/h Baseline Saving</b>: <b>{item['watts_saved']} Watts</b>\n"
                f"⏱️ <b>40 km Time Saved</b>: ~<b>{item['time_saved_40km']}</b>\n"
                f"⚖️ <b>Weight Delta</b>: {wt_str}\n"
                f"💰 <b>Est. Cost</b>: ¥{item['ref_price']} (¥{item['cost_per_watt']}/W)\n"
                f"🏆 <b>Mechanic Score</b>: {item['score']}\n\n"
                f"🛠️ <b>Mechanic Verdict</b>:\n{item['verdict'].get('en', '')}"
            )
        else:
            wt_g = item['weight_save_g']
            wt_str = f"減重 {wt_g}g" if wt_g > 0 else (f"增重 {abs(wt_g)}g" if wt_g < 0 else "無變化")
            text = (
                f"🚀 <b>{item['name'].get('zh_hant', item['id'])}</b>\n"
                f"───────────────────\n"
                f"⚡ <b>40 km/h 基准省瓦</b>：<b>{item['watts_saved']} W</b>\n"
                f"⏱️ <b>40 km 賽道理論省時</b>：約 <b>{item['time_saved_40km']}</b>\n"
                f"⚖️ <b>重量變化</b>：{wt_str}\n"
                f"💰 <b>參考均價</b>：¥{item['ref_price']}（約 ¥{item['cost_per_watt']}/瓦）\n"
                f"🏆 <b>技師推薦指數</b>：{item['score']}\n\n"
                f"🛠️ <b>技師客觀評價</b>：\n{item['verdict'].get('zh_hant', '')}"
            )

        keyboard = [
            [InlineKeyboardButton(t("roi_btn_back", lang=lang), callback_data=f"roi_cat_{cat_id}")],
            [InlineKeyboardButton(t("btn_back_menu", lang=lang), callback_data="main_menu_refresh")]
        ]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        return

async def handle_psi_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理前後輪科學胎壓解算內聯回調"""
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    lang = get_user_lang(user.id, user.language_code)

    # 1. 胎壓選單 / 體重選擇 (psi_menu)
    if data == "psi_menu":
        keyboard = [
            [
                InlineKeyboardButton("55 kg", callback_data="psi_w_55"),
                InlineKeyboardButton("65 kg", callback_data="psi_w_65"),
                InlineKeyboardButton("75 kg", callback_data="psi_w_75"),
                InlineKeyboardButton("85 kg+", callback_data="psi_w_85"),
            ],
            [InlineKeyboardButton(t("btn_back_menu", lang=lang), callback_data="main_menu_refresh")]
        ]
        await query.edit_message_text(
            t("psi_intro", lang=lang),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # 2. 選擇外胎寬度 (psi_w_<weight>)
    if data.startswith("psi_w_"):
        weight_str = data.replace("psi_w_", "")
        weight = float(weight_str)

        keyboard = [
            [
                InlineKeyboardButton("25 mm (25c)", callback_data=f"psi_c_{weight_str}_25"),
                InlineKeyboardButton("28 mm (28c)", callback_data=f"psi_c_{weight_str}_28"),
            ],
            [
                InlineKeyboardButton("30 mm (30c)", callback_data=f"psi_c_{weight_str}_30"),
                InlineKeyboardButton("32 mm (32c)", callback_data=f"psi_c_{weight_str}_32"),
            ],
            [InlineKeyboardButton(t("btn_back_list", lang=lang), callback_data="psi_menu")]
        ]
        await query.edit_message_text(
            t("psi_step_width", lang=lang, weight=int(weight)),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # 3. 計算並生成胎壓卡片 (psi_c_<weight>_<width>)
    if data.startswith("psi_c_"):
        parts = data.split("_")
        weight = float(parts[2])
        width = float(parts[3])

        result = calculate_tire_pressure(weight, width, lang=lang)
        card_text = format_tire_pressure_card(result, lang=lang)

        keyboard = [
            [InlineKeyboardButton("🔄 " + ("Re-calculate" if lang == "en" else "重新計算"), callback_data="psi_menu")],
            [InlineKeyboardButton(t("btn_back_menu", lang=lang), callback_data="main_menu_refresh")]
        ]
        await query.edit_message_text(card_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        return
