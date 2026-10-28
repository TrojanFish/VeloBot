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
- `/roi`: Upgrade Watt Savings & ROI Calculator, evaluating speedsuits, 50mm/60mm carbon wheels, aero cockpits, TPU tubes, hot melt waxed chains, and OSPW pulley systems with wind-tunnel watt savings, 40km time saved, and cost-per-watt ratings.
- `/psi`: Scientific front/rear differential tire pressure calculator (supports fast command `/psi 72 28`). Based on Frank Berto empirical formula and Silca 15% casing deflection model (42% front / 58% rear dynamic load) with Tubeless conversion and Hookless 72.5 PSI safety warning.
- `/calc` & `/chain`: Built-in calculators for chain links (e.g. `/chain 50 34 410`) and tubeless sealant guide.

### 4. 🩺 Cycling Pain Checker & Bike Fitting Rx (/pain)
- Derived from professional Bike Fitting and sports rehabilitation data, covering **6 anatomical areas** (knee, lower back, neck & shoulders, hands & wrists, saddle & perineum, foot numbness).
- Diagnoses across **4 trigger scenarios** (static fit mismatch within 15 mins, endurance fatigue after 2+ hours, climbing torque overload, aggressive aero drop limit).
- 2 clicks generate an instant "Fit Prescription Card": root causes, mechanical cockpit/cleat adjustments, riding posture fixes, and targeted stretches.

### 5. 🛡️ Hardcore Cycling Group Captcha
- Automatically mutes new members upon joining the discussion group.
- Presents a 3-choice road bike tech trivia question (pedal thread directions, Shimano brake mineral oil vs DOT, etc.) with a 120-second timer.
- 100% blocks spam bots while building a hardcore technical community culture.

### 6. 🩺 "Noise Clinic" & Video Submissions (/ask)
- Subscribers can submit 10–15s symptom videos or audios with description.
- **Zero VPS Disk Usage**: Extracts Telegram cloud `file_id` and forwards media directly to host's DM.
- Host replies to the forwarded message in TG to push diagnosis back to the rider. Great source for upcoming video topics!

### 7. 🚲 Bike Maintenance Tracker (/mybike)
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
| `/pain` | Cycling pain self-check & Bike Fitting prescription | Private / Group |
| `/roi` | Upgrade watt savings & ROI calculator (wheels/cockpit/TPU/OSPW) | Private / Group |
| `/psi` | Scientific front/rear differential tire pressure (e.g. `/psi 72 28`) | Private / Group |
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
│   ├── specs_dict.json      # Bilingual road bike specs dictionary (hot reloadable)
│   ├── pain_dict.json       # Bilingual cycling pain & fit prescriptions (hot reloadable)
│   └── upgrade_dict.json    # Bilingual upgrade ROI and watt saving dataset
└── src/
    ├── config.py            # Environment configuration
    ├── database.py          # Database operations
    ├── locales.py           # Bilingual translation dictionary
    ├── utils.py             # Chain calculation, torque/pain/upgrade spec loaders
    ├── bot/
    │   ├── handlers.py      # Command handlers & host reply interceptor
    │   ├── callbacks.py     # Inline keyboard cascading menus & dynamic cards
    │   ├── conversations.py # Noise clinic submission conversation flow
    │   ├── captcha.py       # Group hardcore trivia captcha
    │   └── tasks.py         # Schedulers (YouTube, maintenance alert, backup)
    └── services/
        ├── tire_calc.py     # Scientific differential tire pressure engine
        └── youtube.py       # YouTube RSS listener & enhanced broadcasting
```

---

## 🚀 Quick Deployment (VPS + Docker)

```bash
cp .env.example .env
nano .env
docker compose up -d --build
```

---

## 📄 License
Licensed under the [MIT License](LICENSE).
