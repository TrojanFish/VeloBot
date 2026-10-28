# 🚴 VeloBot 2.0 - Road Bike Mechanic Toolkit & Channel Hub

> A tailored Telegram bot for road bike assembly and maintenance YouTube channels, bike shops, and cycling communities.  
> Transform from a simple broadcast speaker into a **Pocket Mechanic Toolkit + Audience Conversion Hub**.  
> **Languages Supported: Traditional Chinese (繁體中文) & English**

[繁體中文說明文件 (README_zh.md)](README_zh.md)

---

## ✨ Key Features

### 1. 🌐 Bilingual by Design (繁體中文 / English)
- **Automatic Language Detection**: Detects user's Telegram client language automatically or switch anytime via `/lang` or menu buttons.
- **Professional Terminology**: Standard road bike mechanic terminology in both Traditional Chinese (Taiwan & HK conventions) and English.

### 2. 🎬 YouTube Deep Linking & Creator Fast-Binding
- **One Video, One Tool Kit**: Automatically broadcasts new YouTube videos to your Telegram channel with Deep Link buttons (`?start=vid_xxxx`).
- **Private Chat Lookup**: Subscribers click the button to receive featured build tools, torque values, and avoid-pitfall tips directly in private chat.
- **Zero-Console Binding**: When a new video is posted, Bot DMs the channel host. The host simply **Replies to the Telegram notification on mobile** with tool and torque notes. The Bot automatically binds it and pushes it to waiting subscribers!

### 3. 🔧 Pocket Mechanic Toolkit (Pure Inline Keyboard, No Typing)
- `/torque`: Standard torque specs for cockpit, seatpost, drivetrain, BB, disc brakes, cassette, and derailleurs with friction paste & threadlocker safety notes.
- `/bb`: Bottom bracket matching wizard (BSA, BB86, T47 Internal, PF30 for Shimano 24mm, SRAM DUB 28.99mm, Rotor 30mm) with spacer setup and tool guide.
- `/calc` & `/chain`: Built-in calculators for chain links (e.g. `/chain 50 34 410`) and tubeless sealant guide.

### 4. 🛡️ Hardcore Cycling Group Captcha
- Automatically mutes new members upon joining the discussion group.
- Presents a 3-choice road bike tech trivia question (pedal thread directions, Shimano brake mineral oil vs DOT, etc.) with a 120-second timer.
- 100% blocks spam bots while building a hardcore technical community culture.

### 5. 🩺 "Noise Clinic" & Video Submissions (/ask)
- Subscribers can submit 10–15s symptom videos or audios with description.
- **Zero VPS Disk Usage**: Extracts Telegram cloud `file_id` and forwards media directly to host's DM.
- Host replies to the forwarded message in TG to push diagnosis back to the rider. Great source for upcoming video topics!

### 6. 🚲 Bike Maintenance Tracker (/mybike)
- Tracks time-based irreversible degradation (tubeless sealant drying after 90 days, chain hot wax cycles, annual hydraulic brake bleeding).
- Daily 09:00 AM check with 1-click "Done Today" button to reset the timer.
- Daily 03:30 AM automatic SQLite database offsite backup sent directly to the host's Telegram chat.

---

## 🎮 Command Reference

| Command | Description | Context |
| :--- | :--- | :--- |
| `/start` | Launch bot and show visual menu (supports Deep Link args) | Private |
| `/torque` | Instant road bike torque specs (Cockpit/BB/Brakes/Derailleurs) | Private / Group |
| `/bb` | Bottom bracket & crank spindle compatibility wizard | Private / Group |
| `/calc` | Bike assembly calculators (Chain link, Tubeless sealant) | Private / Group |
| `/chain` | Fast chain length calculation (e.g. `/chain 50 34 410`) | Private / Group |
| `/mybike` | Personal periodic maintenance tracker & alerts | Private |
| `/ask` | Noise clinic & troubleshooting media submission | Private |
| `/lang` | Switch bot language (繁體中文 / English) | Private |
| `/help` | View help and documentation | Private / Group |

---

## 🛠️ Project Architecture

```text
VeloBot-main/
├── docker-compose.yml       # Minimal container configuration (no open inbound ports, Long Polling)
├── Dockerfile               # Lightweight Python image
├── requirements.txt         # Core dependencies (python-telegram-bot, feedparser, apscheduler)
├── .env.example             # Environment variable template
├── main.py                  # Entry point, bilingual menu registration, schedulers
├── data/                    # Host persistent directory
│   ├── bot_data.db          # SQLite database (with user language tracking)
│   └── specs_dict.json      # Bilingual road bike specs dictionary (hot reloadable)
└── src/
    ├── config.py            # Environment configuration
    ├── database.py          # Database operations
    ├── locales.py           # Bilingual translation dictionary
    ├── utils.py             # Chain calculation & spec loader
    ├── bot/
    │   ├── handlers.py      # Command handlers & host reply interceptor
    │   ├── callbacks.py     # Inline keyboard cascading menus
    │   ├── conversations.py # Noise clinic submission conversation flow
    │   ├── captcha.py       # Group hardcore trivia captcha
    │   └── tasks.py         # Schedulers (YouTube, maintenance alert, backup)
    └── services/
        └── youtube.py       # YouTube RSS listener & enhanced broadcasting
```

---

## 🚀 Quick Deployment (VPS + Docker)

### 1. Prerequisites
- An overseas VPS (capable of connecting to Telegram API and YouTube RSS).
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather).
- Your personal Telegram numeric ID from [@userinfobot](https://t.me/userinfobot).

### 2. Telegram Group & Channel Permissions
1. **Broadcast Channel**: Add the Bot as an **Administrator** with "Post Messages" permission.
2. **Discussion Group**: Add the Bot as an **Administrator** with:
   - **Restrict Members** (for muting new members during captcha)
   - **Delete Messages** (for auto-cleaning captcha messages)

### 3. Environment Configuration
```bash
cp .env.example .env
nano .env
```

**.env Variables:**
```dotenv
TELEGRAM_BOT_TOKEN=123456789:ABCDEF_your_bot_token
CHANNEL_ID=@YourRoadBikeChannel
GROUP_ID=-1001234567890
ADMIN_ID=987654321
YOUTUBE_CHANNEL_ID=UCxxxxxxxxxxxxxxxxxxxxxx
CHECK_INTERVAL_MINUTES=10
```

### 4. Start Container
```bash
docker compose up -d --build
```

### 5. Inspect Logs
```bash
docker compose logs -f --tail=50
```

---

## 💡 Channel Host Workflow Guide

1. **How to bind video tool kits?**
   - When a new video is published, Bot automatically sends you a private Telegram notification.
   - Simply **Reply to that message** on your phone with tools, torques, or tips. Bot will immediately bind them to the video and notify all waiting subscribers!
2. **How to reply to Noise Clinic tickets?**
   - When a rider submits a 10–15s symptom video via `/ask`, Bot forwards it to your private chat.
   - Simply **Reply to that forwarded message** with your diagnosis. Bot will route the answer back to the rider!
3. **How to update specs without rebuilding?**
   - Edit `./data/specs_dict.json` directly on the host machine. Changes take effect instantly without restarting Docker!

---

## 📄 License
Licensed under the [MIT License](LICENSE).
