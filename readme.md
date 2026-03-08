# 🚴 VeloBot

VeloBot is a powerful, multi-language Telegram bot designed for cycling communities. It integrates with **Strava**, **YouTube**, and **Weather services** to provide a seamless social and training experience for riders worldwide.

[![License](https://img.shields.io/github/license/TrojanFish/VeloBot?color=blue)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/TrojanFish/VeloBot)](https://github.com/TrojanFish/VeloBot/stargazers)
[![Language](https://img.shields.io/badge/Language-Python-green)](https://www.python.org/)

[English](README.md) | [简体中文](README_zh.md)

---

## ✨ Key Features

### 🚴 Strava Deep Integration
- **Activity Tracking**: Automatically push new rides to Telegram groups or private chats.
- **Privacy Support**: Full support for private activities and activities in privacy zones (using `activity:read_all` scope).
- **Scheduled Reports**:
  - **Weekly Report**: Every Monday at 09:00 UTC summarizing last week's performance with a **Suffer Score** trend chart.
  - **Monthly Report**: Every 1st of the month for long-term progress tracking.
  - **Yearly Report**: Every January 1st to celebrate your annual cycling milestones.
- **Group Leaderboards**: Weekly honor roll for Distance, Climbing, and Effort (Time).
- **Achievements**: Unlock medals for milestones like 100km rides, massive climbing, or speed records.
- **Gear Maintenance**: Track mileage for bike components (chains, tires, etc.) and get notified when maintenance is due.

### 📺 Content & Tools
- **YouTube Notifications**: Real-time monitoring of YouTube channels and automatic video sharing.
- **Group Ride Management**: Interactive ride cards for organizing group rides with "Join/Leave" functionality.
- **Weather & Routing**:
  - Cycling-specific weather forecasts based on city name or real-time GPS location.
  - Quick links to route discovery platforms (Komoot, Google Maps).

### 🌍 Global Ready
- **Multi-language Support**: English, Simplified Chinese, Traditional Chinese, Spanish, German, French, and Italian.
- **Unit Conversion**: Easily switch between **Metric** (km, m) and **Imperial** (mi, ft) systems.

---

## 🚀 Deployment Guide

VeloBot is containerized with **Docker** for robust and consistent deployment.

### 1. Prerequisites
- Docker and Docker Compose.
- **Telegram Bot Token**: Get it from [@BotFather](https://t.me/botfather).
- **Strava API Credentials**: Register an application at [Strava Developers](https://www.strava.com/settings/api).
  - *Authorization Callback Domain*: Set this to your server's domain or IP (e.g., `bot.example.com`).

### 2. Setup Instructions
```bash
# Clone the repository
git clone https://github.com/TrojanFish/VeloBot.git
cd VeloBot

# Configure environment variables
cp .env.example .env
# Edit .env and enter your credentials
```

### 3. Start the Bot
```bash
docker-compose up -d --build
```

---

## 🛠️ Configuration (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Token from BotFather | `123456:ABC-DEF...` |
| `TELEGRAM_CHAT_ID` | Group ID for public notifications | `-100123456789` |
| `STRAVA_CLIENT_ID` | Strava API Client ID | `12345` |
| `STRAVA_CLIENT_SECRET` | Strava API Client Secret | `abc123def456...` |
| `BOT_SERVER_URL` | Base URL for OAuth callback | `https://bot.yoursite.com` |
| `YOUTUBE_CHANNEL_ID` | Channel ID to monitor | `UC_xxxxxxxx` |

---

## 🎮 Commands Reference

### General
- `/start` - Initialize the bot and view welcome message.
- `/menu` - Open the interactive visual dashboard.
- `/help` - List all commands and usage.
- `/language` - Switch interface language.
- `/units` - Toggle between Metric and Imperial units.

### Strava
- `/link_strava` - Link your Strava account (Requires re-linking if privacy permissions change).
- `/report` - Manually trigger your personal weekly report.
- `/leaderboard` - View group weekly rankings.
- `/sync_strava` - Manually sync recent activities and gear details.
- `/toggle_strava_privacy` - Choose if your activities are posted publicly to the group or sent privately.

### Utility
- `/weather [city]` - Check riding weather.
- `/route [location]` - Generate route planning links.
- `/create_ride` - Start a step-by-step group ride organization.

---

## 📁 Project Architecture
```text
VeloBot/
├── main.py              # Bot entry point and scheduler
├── src/
│   ├── bot/             # Telegram handlers, tasks, and callbacks
│   │   ├── handlers.py  # Command logic
│   │   └── tasks.py     # Background sync & periodic reports
│   ├── services/        # Third-party API integrations (Strava, YT, Weather)
│   ├── web/             # Flask server for Strava OAuth
│   └── locales.py       # Translation strings
├── data/                # Persistent SQLite database & cache
└── docker-compose.yml   # Container orchestration
```

## 🔒 Security & Performance
- **Non-root Execution**: Runs as `botuser` in Docker for security.
- **Asynchronous Processing**: Powered by `python-telegram-bot`'s async framework.
- **Data Persistence**: Uses SQLite with volume mapping to local `./data` folder.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.