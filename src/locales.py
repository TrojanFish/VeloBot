# ========================================================
# VeloBot 2.0 雙語文案字典 (繁體中文 zh_hant & 英文 en)
# ========================================================

TRANSLATIONS = {
    "zh_hant": {
        # 歡迎與主選單
        "welcome": (
            "👋 你好，**{name}**！歡迎使用 **公路車技師口袋工具箱** 🚴‍♂️\n\n"
            "裝車調車手上沾滿黃油？不用再狼狽翻說明書或搜尋長影片，Bot 隨時為你提供關鍵參數秒查！\n\n"
            "🛠️ **常用技師指令：**\n"
            "• /torque - 關鍵部位標準鎖緊扭力速查\n"
            "• /bb - 五通規格與大盤軸心相容匹配器\n"
            "• /pain - 騎行疼痛自查與 Fitting 處方籤\n"
            "• /calc - 鏈條節數與無內胎補胎液推薦計算器\n"
            "• /mybike - 個人車輛週期保養打卡與提醒\n"
            "• /ask - 異音門診與組裝疑難雜症投稿\n"
            "• /lang - 切換語言 (繁體中文 / English)\n\n"
            "頻道新影片上映時，頻道消息底部將附帶直達按鈕，為你推送一影片一專屬工具清單！"
        ),
        "btn_torque": "🔧 扭力速查",
        "btn_bb": "⚙️ 五通匹配器",
        "btn_pain": "🩺 疼痛自查",
        "btn_calc": "📐 組裝計算器",
        "btn_mybike": "🚲 保養管家",
        "btn_ask": "🩺 異音門診投稿",
        "btn_lang": "🌐 語言 / Language",
        "btn_watch_yt": "🎬 觀看 YouTube 影片",
        "btn_get_kit": "🔧 獲取本期工具與扭力清單",
        "btn_notify_waitlist": "🔔 本期清單更新後通知我",
        "btn_back_menu": "🔙 返回主選單",
        "btn_back_list": "🔙 返回列表",

        # 疼痛自查
        "pain_intro": (
            "🩺 **公路車騎行疼痛與 Fitting 自查工具**\n\n"
            "騎車哪裡不舒服？膝蓋痛、腰背酸、手掌麻木或坐墊壓迫？\n"
            "請依序點選，Bot 將為你輸出病因診斷、車輛設定調整、騎乘姿勢修正與專案拉伸動作！\n\n"
            "👉 **第 1 步：請點選出現疼痛或麻木的部位：**"
        ),
        "pain_step2": (
            "🩺 當前所選部位：**{area}**\n\n"
            "👉 **第 2 步：請問疼痛或不適通常在什麼情境下出現？**"
        ),
        "pain_btn_restart": "🔄 查詢其他部位",
        "pain_btn_ask": "🩺 提交異音/門診",

        # 語言切換
        "lang_switch_prompt": "🌐 請選擇你的偏好語言 / Please select your preferred language:",
        "lang_switched": "✅ 已成功切換為：**繁體中文**！",

        # 影片物料
        "video_kit_title": "🔧 **《{title}》專屬組裝工具與扭力避坑清單**\n\n{content}\n\n🎬 [點擊在 YouTube 觀看本期完整影片](https://www.youtube.com/watch?v={video_id})",
        "video_kit_preparing": (
            "🛠️ **《{title}》專屬工具與扭力清單正在整理中！**\n\n"
            "台長正在加緊錄入本期出鏡的專用工具型號、各部件鎖緊扭力與避坑指南。\n\n"
            "👇 點擊下方按鈕預約，台長錄入後 Bot 將第一時間私信通知你！"
        ),
        "waitlist_success": "🔔 預約成功！當台長錄入該期工具與扭力清單後，Bot 會第一時間私信補發給你！",
        "waitlist_broadcast": "🔔 **你預約的《{title}》專屬工具與扭力清單已更新！**\n\n{content}\n\n🎬 [點擊在 YouTube 觀看完整影片](https://www.youtube.com/watch?v={video_id})",

        # 扭力速查
        "torque_title": "🔧 **公路車關鍵部位標準扭力速查**\n\n請點選想要查詢的系統組件：",
        "torque_warning": "⚠️ *技師提醒：組裝時請務必確認是否需塗抹碳纖維止滑膏或螺絲膠，嚴禁蠻力超扭！*",

        # 五通匹配器
        "bb_title": "⚙️ **公路車五通與大盤軸心匹配器 (BB Matcher)**\n\n👉 **第 1 步：請選擇車架五通規格：**",
        "bb_step2": "⚙️ 當前所選五通：**{frame}**\n\n👉 **第 2 步：請選擇你打算安裝的大盤軸心規格：**",
        "bb_result_title": "⚙️ **匹配結果方案：**\n\n{content}",
        "bb_no_match": "⚠️ 暫無該規格的具體匹配數據，或該五通結構不支援直接相容此軸心規格。",

        # 計算器
        "calc_title": "📐 **公路車實用組裝計算器**\n\n請選擇你想計算的項目：",
        "calc_btn_chain": "📏 鏈條節數計算與指引",
        "calc_btn_tubeless": "🥛 無內胎補胎液推薦量",
        "chain_usage": (
            "📏 **鏈條長度計算器**\n\n"
            "用法：`/chain <大盤最大齒數> <最大飛輪齒數> <後下叉長度mm>`\n\n"
            "例如：`/chain 50 34 410`\n"
            "（若不清楚後下叉長度，常見公路車通常在 405~415mm 之間）"
        ),
        "chain_result": (
            "📏 **鏈條標準節數推算結果：**\n\n"
            "• **大盤齒數**：{big}T\n"
            "• **最大飛輪齒數**：{max_cog}T\n"
            "• **後下叉長度**：{chainstay} mm\n\n"
            "✅ **推薦鏈條長度**：**`{links}` 節**（含快扣/魔術扣，標準偶數節）\n\n"
            "💡 *實操提示*：截鏈前建議將鏈條穿過大盤和最大飛輪（不穿後變速器導輪），兩端拉緊重疊後預留 2 節作為雙重確認！"
        ),
        "chain_error": "❌ 參數格式錯誤，請輸入純數字。例如：`/chain 50 34 410`",

        # 保養管家
        "mybike_title": "🚲 **個人車輛週期性保養管家**\n\n",
        "mybike_log_item": "• **{label}**\n  上次打卡：`{last_date}` ｜ 下次提醒：`{next_date}`\n\n",
        "mybike_unrecorded": "• **{label}**：暫未打卡（週期 {cycle} 天）\n\n",
        "mybike_btn_done": "✅ 今日已完成：{label}",
        "mybike_done_alert": "✅ 已記錄！已為你重置 {label} 的到期提醒（{cycle}天後）。",
        "mybike_reminder_text": (
            "🔔 **公路車定期保養到期提醒**\n\n"
            "🛠️ **項目**：{label}\n"
            "📅 **上次打卡日期**：`{last_date}`\n"
            "💡 **保養建議**：{desc}\n\n"
            "如果今日已完成保養，可直接點擊下方按鈕重置提醒週期："
        ),
        "mybike_reminder_btn": "✅ 今日已完成保養（重置週期）",

        # 異音門診
        "ask_intro": (
            "🩺 **公路車異音與疑難雜症門診**\n\n"
            "裝車調車遇到搞不定的異音？或是煞車蹭碟、變速跳齒？\n"
            "請按步驟提交你的故障實況，台長將親自為你診斷答疑，典型案例還將收錄進下期影片選題！\n\n"
            "👉 **第 1 步：請點選出現異音或故障的部位：**\n"
            "（如需退出請隨時發送 /cancel）"
        ),
        "ask_step2": (
            "✅ 已選擇部位：**{part}**\n\n"
            "👉 **第 2 步：請上傳一段 10–15 秒的實況影片、音訊或特寫照片**\n\n"
            "💡 **錄製建議**：\n"
            "• 儘量將手機靠近異音發出的位置（如五通、卡鉗）\n"
            "• 錄製時請避開強烈風噪環境\n"
            "• 若暫時沒有影音資料，可發送 /skip 跳過"
        ),
        "ask_step3": (
            "✅ 影音資料已接收！\n\n"
            "👉 **第 3 步：請簡要描述異音發生的場景與規律**\n\n"
            "例如：\n"
            "• *'只有站姿大力抽車踩左腳時出現喀嗒聲，坐姿踩踏完全正常'*\n"
            "• *'下坡高速重煞前輪劇烈抖動伴隨高頻尖叫'*\n\n"
            "請直接回覆文字完成提交："
        ),
        "ask_skipped": "⏩ 已跳過媒體上傳。\n\n👉 **第 3 步：請盡可能詳細地描述異音發生的場景與規律**：",
        "ask_submitted": (
            "🎉 **異音工單 #{ticket_id} 提交成功！**\n\n"
            "台長已經收到你的故障影像與描述。\n"
            "台長診斷分析後，Bot 將會第一時間把答覆推送給你。\n"
            "同時，該案例也有可能成為頻道下期裝車避坑影片的實戰素材！"
        ),
        "ask_canceled": "已取消異音投稿流程。隨時可再次發送 /ask 啟動！",

        # 入群驗證
        "captcha_prompt": (
            "👋 歡迎 [{name}](tg://user?id={user_id}) 加入技術討論群！\n\n"
            "🛡️ **為防範廣告機器人，請在 120 秒內回答一道公路車常識題：**\n\n"
            "❓ **{question}**"
        ),
        "captcha_correct": "🎉 回答正確！公路車技師認證通過！",
        "captcha_passed_msg": "✅ [{name}](tg://user?id={user_id}) 驗證通過，歡迎加入技術討論！",
        "captcha_wrong": "❌ 回答錯誤！公路車技師認證未通過。",
        "captcha_not_you": "⚠️ 這不是屬於你的驗證題，請勿亂點！"
    },

    "en": {
        # Welcome & Main Menu
        "welcome": (
            "👋 Hello, **{name}**! Welcome to the **Road Bike Mechanic Toolkit** 🚴‍♂️\n\n"
            "Greasy hands while building or tuning your bike? No need to struggle through heavy manuals or long videos. Get instant technical specs right here!\n\n"
            "🛠️ **Commands:**\n"
            "• /torque - Standard torque values lookup\n"
            "• /bb - Bottom bracket & crank spindle compatibility wizard\n"
            "• /pain - Cycling pain checker & Bike Fit prescription\n"
            "• /calc - Chain length & tubeless sealant calculators\n"
            "• /mybike - Personal periodic maintenance tracker & alerts\n"
            "• /ask - Road bike noise clinic & symptom submission\n"
            "• /lang - Switch language (繁體中文 / English)\n\n"
            "Whenever a new video is published, interactive buttons will deliver the exact tool list and torque values straight to your chat!"
        ),
        "btn_torque": "🔧 Torque Lookup",
        "btn_bb": "⚙️ BB Matcher",
        "btn_pain": "🩺 Pain Checker",
        "btn_calc": "📐 Calculators",
        "btn_mybike": "🚲 Maintenance",
        "btn_ask": "🩺 Noise Clinic",
        "btn_lang": "🌐 Language / 語言",
        "btn_watch_yt": "🎬 Watch on YouTube",
        "btn_get_kit": "🔧 Get Video Tool & Torque List",
        "btn_notify_waitlist": "🔔 Notify me when updated",
        "btn_back_menu": "🔙 Main Menu",
        "btn_back_list": "🔙 Back",

        # Pain Checker
        "pain_intro": (
            "🩺 **Road Bike Pain Checker & Bike Fitting Prescription**\n\n"
            "Suffering from knee pain, back ache, hand numbness, or saddle soreness?\n"
            "Follow the prompts to diagnose causes, mechanical fit adjustments, riding form fixes, and targeted stretches!\n\n"
            "👉 **Step 1: Select the troubled anatomical area:**"
        ),
        "pain_step2": (
            "🩺 Selected Area: **{area}**\n\n"
            "👉 **Step 2: When does the pain or discomfort typically occur?**"
        ),
        "pain_btn_restart": "🔄 Check Another Area",
        "pain_btn_ask": "🩺 Ask Mechanic",

        # Language Switch
        "lang_switch_prompt": "🌐 Please select your preferred language / 請選擇語言：",
        "lang_switched": "✅ Language successfully set to: **English**!",

        # Video Materials
        "video_kit_title": "🔧 **《{title}》Exclusive Tools & Torque Sheet**\n\n{content}\n\n🎬 [Watch full build video on YouTube](https://www.youtube.com/watch?v={video_id})",
        "video_kit_preparing": (
            "🛠️ **《{title}》Tool and torque sheet is being prepared!**\n\n"
            "The channel host is currently recording featured tools, tightening torques, and build tips.\n\n"
            "👇 Click below to subscribe; Bot will deliver it to you as soon as it's ready!"
        ),
        "waitlist_success": "🔔 Subscribed! Bot will deliver the tool and torque list as soon as the host publishes it!",
        "waitlist_broadcast": "🔔 **《{title}》Tool & Torque Sheet is Ready!**\n\n{content}\n\n🎬 [Watch on YouTube](https://www.youtube.com/watch?v={video_id})",

        # Torque Lookup
        "torque_title": "🔧 **Road Bike Standard Torque Lookup**\n\nSelect a component system to inspect:",
        "torque_warning": "⚠️ *Mechanic Note: Always verify if carbon friction paste or threadlocker is required. Never over-torque!*",

        # BB Matcher
        "bb_title": "⚙️ **Road Bike Bottom Bracket Matcher**\n\n👉 **Step 1: Select your frame bottom bracket standard:**",
        "bb_step2": "⚙️ Selected BB Shell: **{frame}**\n\n👉 **Step 2: Select your crankset spindle standard:**",
        "bb_result_title": "⚙️ **Compatibility Solution:**\n\n{content}",
        "bb_no_match": "⚠️ No direct match data available or the shell is incompatible with this spindle.",

        # Calculators
        "calc_title": "📐 **Road Bike Assembly Calculators**\n\nSelect a tool:",
        "calc_btn_chain": "📏 Chain Length Calculation",
        "calc_btn_tubeless": "🥛 Tubeless Sealant Guide",
        "chain_usage": (
            "📏 **Chain Length Calculator**\n\n"
            "Usage: `/chain <big_chainring> <max_rear_cog> <chainstay_mm>`\n\n"
            "Example: `/chain 50 34 410`\n"
            "(Standard road chainstay length is usually between 405~415mm)"
        ),
        "chain_result": (
            "📏 **Recommended Chain Length:**\n\n"
            "• **Big Chainring**: {big}T\n"
            "• **Max Cassette Cog**: {max_cog}T\n"
            "• **Chainstay Length**: {chainstay} mm\n\n"
            "✅ **Recommended Links**: **`{links}` links** (including quick-link, even number)\n\n"
            "💡 *Tip*: Before breaking the chain, wrap it around big-big (bypassing rear derailleur), pull tight and add 2 links as double verification!"
        ),
        "chain_error": "❌ Invalid format. Please enter numeric values, e.g. `/chain 50 34 410`",

        # Maintenance Tracker
        "mybike_title": "🚲 **Personal Road Bike Maintenance Tracker**\n\n",
        "mybike_log_item": "• **{label}**\n  Last logged: `{last_date}` | Next due: `{next_date}`\n\n",
        "mybike_unrecorded": "• **{label}**: Not logged yet (Cycle: {cycle} days)\n\n",
        "mybike_btn_done": "✅ Done today: {label}",
        "mybike_done_alert": "✅ Recorded! Next reminder for {label} reset to {cycle} days later.",
        "mybike_reminder_text": (
            "🔔 **Road Bike Maintenance Due Reminder**\n\n"
            "🛠️ **Task**: {label}\n"
            "📅 **Last Serviced**: `{last_date}`\n"
            "💡 **Advice**: {desc}\n\n"
            "If completed today, click below to reset your cycle:"
        ),
        "mybike_reminder_btn": "✅ Done Today (Reset Cycle)",

        # Noise Clinic
        "ask_intro": (
            "🩺 **Road Bike Noise & Troubleshooting Clinic**\n\n"
            "Encountering mysterious creaks, clicks, or rubbing brakes?\n"
            "Submit your symptoms step-by-step; the host will diagnose it and featured cases will be covered in upcoming build videos!\n\n"
            "👉 **Step 1: Select the troubled component area:**\n"
            "(Type /cancel at any time to exit)"
        ),
        "ask_step2": (
            "✅ Selected Area: **{part}**\n\n"
            "👉 **Step 2: Upload a 10–15s video, audio, or close-up photo**\n\n"
            "💡 **Recording Tips**:\n"
            "• Hold the microphone close to the suspected source (e.g. BB, caliper)\n"
            "• Avoid heavy wind noise\n"
            "• Send /skip if you don't have media ready"
        ),
        "ask_step3": (
            "✅ Media received!\n\n"
            "👉 **Step 3: Briefly describe when and how the noise occurs**\n\n"
            "Examples:\n"
            "• *'Clicking only when out of saddle pressing hard on the left pedal'*\n"
            "• *'High-speed heavy front braking causes severe shutter and squeal'*\n\n"
            "Send your text to complete submission:"
        ),
        "ask_skipped": "⏩ Media upload skipped.\n\n👉 **Step 3: Please describe the symptom in detail**:",
        "ask_submitted": (
            "🎉 **Troubleshooting Ticket #{ticket_id} submitted!**\n\n"
            "The channel host has received your media and details.\n"
            "You will receive diagnostic feedback directly via this Bot!\n"
            "High-value cases may also be featured in upcoming YouTube videos!"
        ),
        "ask_canceled": "Submission canceled. Type /ask anytime to start over!",

        # Captcha
        "captcha_prompt": (
            "👋 Welcome [{name}](tg://user?id={user_id}) to the community!\n\n"
            "🛡️ **To prevent spam bots, please answer this road bike trivia within 120s:**\n\n"
            "❓ **{question}**"
        ),
        "captcha_correct": "🎉 Correct! Welcome aboard!",
        "captcha_passed_msg": "✅ [{name}](tg://user?id={user_id}) verified! Welcome to the technical discussion!",
        "captcha_wrong": "❌ Incorrect answer! Verification failed.",
        "captcha_not_you": "⚠️ This question is not for you!"
    }
}

def t(key: str, lang: str = "zh_hant", **kwargs) -> str:
    """獲取本地化文案，支持參數格式化"""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["zh_hant"])
    template = lang_dict.get(key, TRANSLATIONS["zh_hant"].get(key, key))
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
