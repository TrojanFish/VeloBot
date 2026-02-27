# 🚴 VeloBot

VeloBot is a powerful, multi-language Telegram bot designed for cycling communities. It integrates with **Strava**, **YouTube**, and **Weather services** to provide a seamless social experience for riders worldwide.

## ✨ Features

- 🌍 **Multi-language Support**: Supports English, Simplified Chinese, Traditional Chinese, Spanish, German, French, and Italian.
- 🚴 **Strava Integration**: 
  - Automatically push new activities to Telegram groups or private messages.
  - Personal weekly reports and group leaderboards.
  - Achievement system (e.g., first 100km ride, 1000m climbing).
- 📺 **YouTube Notifications**: Monitor YouTube channels and push new videos to the group automatically.
- 🤝 **Group Ride Organization**: Create, join, and manage group rides with interactive cards.
- 🌦️ **Weather Forecasts**: Get cycling-specific weather forecasts by city or real-time location.
- 🗺️ **Route Discovery**: Find cycling routes in various platforms (Google Maps, Komoot) based on location.

## 🚀 Deployment

VeloBot is containerized with **Docker** for easy deployment on any VPS.

### Prerequisites

- Docker and Docker Compose installed.
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather)).
- Strava API credentials (from [Strava Developers](https://www.strava.com/settings/api)).

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/TrojanFish/VeloBot.git
   cd VeloBot
   ```

2. **Configure Environment Variables**:
   Copy the example environment file and fill in your credentials.
   ```bash
   cp .env.example .env
   # Edit .env with your favorite editor
   ```

3. **Start with Docker Compose**:
   ```bash
   docker-compose up -d --build
   ```

## 🛠️ Configuration (.env)

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | The ID of the group/channel for public pushes |
| `STRAVA_CLIENT_ID` | Strava API Client ID |
| `STRAVA_CLIENT_SECRET` | Strava API Client Secret |
| `BOT_SERVER_URL` | Public URL of your bot (for Strava OAuth callback) |
| `YOUTUBE_CHANNEL_ID` | ID of the YouTube channel to monitor |

## 📁 Project Structure

- `src/`: Core source code.
  - `bot/`: Telegram bot handlers, callbacks, and tasks.
  - `services/`: Strava, YouTube, and Weather API integrations.
  - `web/`: Flask server for handling Strava OAuth.
  - `locales.py`: Internationalization and translation database.
  - `database.py`: SQLite database management.

## 🔒 Security

- The application runs as a **non-root user** inside the Docker container.
- Sensitive information is managed via environment variables and never hardcoded.

## 📄 License

This project is licensed under the MIT License.