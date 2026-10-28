# 🚴 VeloBot 2.0 - 公路車技師口袋工具箱與頻道中樞

> 專為公路車組裝與保養 YouTube 頻道、技師工作坊與車友社群量身定制的 Telegram 機器人。  
> 告別單向推播與臃腫雜貨鋪，打造「車友裝車口袋工具箱 + 影片內容私域沉澱中樞」。  
> **語言支援：繁體中文 (Traditional Chinese) ｜ English**

[English Documentation (README.md)](readme.md)

---

## ✨ 核心特性

### 1. 🌐 雙語原生支援 (繁體中文 / English)
- **智慧語言探測**：依據車友的 Telegram 客戶端設定自動切換為繁體中文或英文。
- **隨時隨地手動切換**：發送 `/lang` 或點擊主選單 `[🌐 語言 / Language]` 即可一鍵切換。
- **公路車專業術語本地化**：嚴格採用台灣/香港及國際標準公路車技師術語（龍頭、車把、座管、五通、反牙、止滑膏、螺絲膠等）。

### 2. 🎬 YouTube 影片深度聯動（Deep Linking 精準分發）
- **一影片一工具清單**：新影片自動推播至 Telegram 頻道，底部附帶專屬 Deep Link 按鈕（`?start=vid_xxxx`）。
- **車友私聊秒查**：車友點擊按鈕，自動跳轉私聊獲取本期出鏡工具型號、專屬扭力清單與裝車避坑提示。
- **台長免後台一鍵綁定**：影片發布後，Bot 自動私信台長；**台長直接長按【回覆/Reply】該通知**貼上物料，Bot 即可自動完成綁定並給等待中的車友補發！

### 3. 🔧 技師口袋速查器（純內聯按鈕點選，無須打字）
- `/torque`：公路車各部位標準扭力速查（龍頭車把、座管、大盤中軸、碟煞、飛輪、變速），自帶碳纖維止滑膏/螺絲膠安全提示。
- `/bb`：五通規格與大盤軸心相容匹配器（BSA、BB86、T47、PF30 等相容 Shimano 24、SRAM DUB 28.99、30mm），輸出適配型號、墊圈配置與拆裝工具。
- `/calc` 與 `/chain`：裝車計算器（鏈條標準節數推算、無內胎補胎液推薦量）。

### 4. 🛡️ 硬核公路車入群驗證（Group Captcha）
- 新人加入討論群自動禁言（Mute），Bot 發送 3 選 1 公路車硬核常識題（如踏板拆卸旋轉方向、Shimano 煞車油類型等）。
- 120 秒倒計時，答對立即解禁並自動銷毀提示，答錯或超時自動踢出。
- 100% 抵禦廣告機器人，在進群第一秒樹立硬核技術討論氛圍。

### 5. 🩺 異音門診與選題反哺（/ask）
- 車友在私聊可上傳 10-15 秒故障影片/音訊並補充文字。
- **零 VPS 硬碟佔用**：提取 Telegram 雲端 `file_id`，原樣轉發至台長私聊。
- **台長快捷回覆**：台長在手機端長按【回覆/Reply】工單，Bot 自動將診斷建議推回給提問車友，同時沉澱為下期影片的選題庫。

### 6. 🚲 個人車輛週期性保養管家（/mybike）
- 追蹤時間維度的老化風險（無內胎補胎液 90 天必乾、鏈條熱浸蠟、煞車油防吸水變質）。
- 每日早上 09:00 自動檢查到期記錄並推播私信，附帶一鍵「今日已完成」重置週期按鈕。
- 每日凌晨 03:30 自動將 SQLite 資料庫打包發送到台長私聊，實現零成本異地容災備份。

---

## 🎮 常用指令一覽表

| 指令 | 說明 | 適用場景 |
| :--- | :--- | :--- |
| `/start` | 啟動機器人並呼出主選單（支援 Deep Link 參數） | 私聊 |
| `/torque` | 關鍵部位標準鎖緊扭力速查（龍頭/車把/座管/大盤/碟煞/變速） | 私聊 / 群組 |
| `/bb` | 五通規格與大盤軸心相容匹配指南（墊圈配置與專用工具） | 私聊 / 群組 |
| `/calc` | 組裝實用計算器選單（鏈條計算、補胎液指南） | 私聊 / 群組 |
| `/chain` | 快速計算鏈條標準節數（例如 `/chain 50 34 410`） | 私聊 / 群組 |
| `/mybike` | 個人車輛週期保養打卡與到期提醒管家 | 私聊 |
| `/ask` | 異音門診與裝車故障影音投稿 | 私聊 |
| `/lang` | 切換機器人語言（🇹🇼 繁體中文 / 🇬🇧 English） | 私聊 |
| `/help` | 查閱指令說明與使用指南 | 私聊 / 群組 |

---

## 🛠️ 專案架構

```text
VeloBot-main/
├── docker-compose.yml       # 極簡容器編排（零外部端口暴露，長輪詢運行）
├── Dockerfile               # 輕量 Python 映像檔
├── requirements.txt         # 核心依賴 (python-telegram-bot, feedparser, apscheduler)
├── .env.example             # 環境變數範本
├── main.py                  # 機器人主入口、雙語選單註冊與排程器
├── data/                    # 宿主機掛載目錄（資料持久化）
│   ├── bot_data.db          # SQLite 業務資料庫 (含語言偏好記錄)
│   └── specs_dict.json      # 繁中/英文公路車參數字典與入群題庫（支援熱編輯）
└── src/
    ├── config.py            # 配置管理
    ├── database.py          # 資料庫 CRUD 與用戶語言記憶
    ├── locales.py           # 繁體中文與英文雙語文字字典
    ├── utils.py             # 鏈條公式推算與字典讀取
    ├── bot/
    │   ├── handlers.py      # 命令入口、語言切換與管理員 Reply 攔截器
    │   ├── callbacks.py     # 級聯內聯鍵盤與雙語動態渲染
    │   ├── conversations.py # 異音門診雙語互動狀態機
    │   ├── captcha.py       # 入群硬核問答驗證與倒計時踢出
    │   └── tasks.py         # 定時任務（YouTube 監聽、保養提醒、異地備份）
    └── services/
        └── youtube.py       # YouTube RSS 監聽與雙語增強型推播
```

---

## 🚀 部署指引 (VPS + Docker)

### 1. 前置準備
- 一台海外 VPS（如新加坡、美西、東京等，可直連 Telegram API 與 YouTube RSS）。
- 一個 Telegram 機器人 Token（向 [@BotFather](https://t.me/BotFather) 申請）。
- 你的個人 Telegram 數字 ID（透過 [@userinfobot](https://t.me/userinfobot) 獲取）。

### 2. Telegram 群組與頻道權限設定
1. **廣播頻道**：將 Bot 新增為頻道管理員（Administrator），給予「發布消息 (Post Messages)」權限。
2. **討論群組**：將 Bot 新增為討論群管理員，並勾選以下權限：
   - 封鎖使用者 / 限制成員（**Restrict Members**，用於新成員入群答題禁言）
   - 刪除消息（**Delete Messages**，用於定時銷毀答題卡）

### 3. 配置環境變數
```bash
cp .env.example .env
nano .env
```

**.env 變數說明：**
```dotenv
# 機器人 Token
TELEGRAM_BOT_TOKEN=123456789:ABCDEF_your_bot_token

# 頻道 ID（例如 @YourRoadBikeChannel 或 -100xxxxxxxxxx）
CHANNEL_ID=@YourRoadBikeChannel

# 討論群組數字 ID（例如 -100xxxxxxxxxx）
GROUP_ID=-1001234567890

# 台長個人 Telegram 數字 ID
ADMIN_ID=987654321

# YouTube 頻道 ID (UCxxxxxxxxxxxxxxxxxxxxxx)
YOUTUBE_CHANNEL_ID=UCxxxxxxxxxxxxxxxxxxxxxx

# YouTube 輪詢週期（分鐘，預設 10）
CHECK_INTERVAL_MINUTES=10
```

### 4. 啟動容器
```bash
docker compose up -d --build
```

### 5. 查看日誌
```bash
docker compose logs -f --tail=50
```

---

## 💡 台長日常操作指南

### 1. 如何錄入新影片工具物料？
1. YouTube 發布新影片後，Bot 監測到新片會自動推播至你的 Telegram 頻道。
2. 與此同時，Bot 會向你的個人 Telegram 私信發送一條催更通知。
3. **在手機 Telegram 上長按【回覆/Reply】該通知**，直接貼上文字（如工具型號、鎖緊扭力、避坑注意事項），Bot 會立刻將其存入資料庫，並自動推送給已預約該影片清單的車友！

### 2. 如何回覆車友的異音工單？
1. 車友透過 `/ask` 提交 10-15 秒影片及故障描述後，Bot 會自動將影片與資訊轉發至你的個人私聊。
2. **長按【回覆/Reply】該工單消息**輸入你的診斷建議，Bot 便會以機器人名義私信回傳給該車友，工單自動歸檔！

### 3. 如何自訂修改扭力或五通規格？
直接在宿主機編輯 `./data/specs_dict.json` 即可：
```bash
nano data/specs_dict.json
```
修改後儲存即刻生效，**無須重啟 Docker 容器**。

---

## 📄 License
本專案採用 [MIT License](LICENSE) 開源授權。
