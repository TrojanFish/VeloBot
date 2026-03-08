# 🚴 VeloBot (骑行机器人)

VeloBot 是一款功能强大、支持多语言的 Telegram 机器人，专为骑行社群设计。它集成了 **Strava**、**YouTube** 和 **天气服务**，为全球骑手提供无缝的社交和训练体验。

[![License](https://img.shields.io/github/license/TrojanFish/VeloBot?color=blue)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/TrojanFish/VeloBot)](https://github.com/TrojanFish/VeloBot/stargazers)
[![Language](https://img.shields.io/badge/Language-Python-green)](https://www.python.org/)

[English](README.md) | [简体中文](README_zh.md)

---

## ✨ 核心功能

### 🚴 Strava 深度集成
- **活动追踪**：自动将新的骑行活动推送到 Telegram 群组或私聊。
- **隐私支持**：完美支持私人活动和隐私区域活动（使用 `activity:read_all` 权限范围）。
- **定期报表**：
  - **周报**：每周一 UTC 09:00（北京时间 17:00）自动推送上周表现汇总，包含 **Suffer Score (受累分)** 趋势图。
  - **月报**：每月 1 号生成，追踪长期训练进度。
  - **年报**：每年 1 月 1 日生成，回顾年度骑行里程碑。
- **群组光荣榜**：每周统计并排名距离之王、爬坡之王和劳模之王（运动时间）。
- **成就系统**：解锁里程碑勋章，如首次百公里骑行、千米爬升或速度记录。
- **器材维护**：记录自行车配件（链条、外胎等）的里程，并在需要保养时发送提醒。

### 📺 内容与工具
- **YouTube 订阅**：实时监控 YouTube 频道，自动分享最新视频。
- **约骑管理**：交互式约骑卡片，支持“加入/退出”功能，轻松组织群组约骑。
- **天气与路线**：
  - 提供针对骑行优化的天气预报（支持城市名或实时 GPS 位置）。
  - 快速生成热门路线平台（Komoot, Google Maps）的规划链接。

### 🌍 全球化设计
- **多语言支持**：简体中文、繁体中文、英语、西班牙语、德语、法语和意大利语。
- **单位转换**：可在 **公制** (km, m) 和 **英制** (mi, ft) 系统间自由切换。

---

## 🚀 部署指南

VeloBot 采用 **Docker** 容器化部署，确保在任何环境下都能稳定运行。

### 1. 前置条件
- 已安装 Docker 和 Docker Compose。
- **Telegram Bot Token**：从 [@BotFather](https://t.me/botfather) 获取。
- **Strava API 凭据**：在 [Strava Developers](https://www.strava.com/settings/api) 注册应用。
  - *重定向 URL (Authorization Callback Domain)*：设置为你服务器的域名或 IP（例如 `bot.example.com`）。

### 2. 安装步骤
```bash
# 克隆仓库
git clone https://github.com/TrojanFish/VeloBot.git
cd VeloBot

# 配置环境变量
cp .env.example .env
# 使用编辑器修改 .env 并填写你的 API 凭据
```

### 3. 启动机器人
```bash
docker-compose up -d --build
```

---

## 🛠️ 环境变量配置 (.env)

| 变量名 | 描述 | 示例 |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | 后台申请的机器人 Token | `123456:ABC-DEF...` |
| `TELEGRAM_CHAT_ID` | 公开推送的目标群组 ID | `-100123456789` |
| `STRAVA_CLIENT_ID` | Strava 应用 Client ID | `12345` |
| `STRAVA_CLIENT_SECRET` | Strava 应用密钥 | `abc123def456...` |
| `BOT_SERVER_URL` | 用于 OAuth 回调的基础 URL | `https://bot.yoursite.com` |
| `YOUTUBE_CHANNEL_ID` | 要监控的 YouTube 频道 ID | `UC_xxxxxxxx` |

---

## 🎮 常用命令说明

### 通用命令
- `/start` - 初始化机器人并查看欢迎信息。
- `/menu` - 打开交互式图形化控制面板。
- `/help` - 查看所有命令列表。
- `/language` - 切换界面语言。
- `/units` - 切换公制/英制单位。

### Strava 相关
- `/link_strava` - 绑定 Strava 账号（如果权限变更，需要重新绑定）。
- `/report` - 手动生成个人周报。
- `/leaderboard` - 查看群组每周排名。
- `/sync_strava` - 手动同步最近活动和器材信息。
- `/toggle_strava_privacy` - 选择活动是公开推送到群组还是仅私聊发送。

### 实用工具
- `/weather [城市]` - 查询骑行天气。
- `/route [地点]` - 生成路线规划链接。
- `/create_ride` - 按照指引创建一次约骑活动任务。

---

## 📁 项目结构
```text
VeloBot/
├── main.py              # 入口程序与定时任务调度
├── src/
│   ├── bot/             # Telegram 处理器、任务和回调
│   │   ├── handlers.py  # 命令逻辑
│   │   └── tasks.py     # 后台同步与定期报表
│   ├── services/        # 第三方 API 集成 (Strava, YT, 天气)
│   ├── web/             # 用于处理 Strava OAuth 的 Flask 服务器
│   └── locales.py       # 多语言翻译文本
├── data/                # 持久化 SQLite 数据库与缓存
└── docker-compose.yml   # 容器编排配置
```

## 🔒 安全与性能
- **非 Root 运行**：Docker 镜像内以 `botuser` 身份运行，提升安全性。
- **异步处理**：基于 `python-telegram-bot` 异步框架开发。
- **数据持久化**：使用 SQLite 数据库，并映射到宿主机的 `./data` 文件夹。

## 📄 开源协议
本项目采用 MIT 协议开源 - 详情请参阅 [LICENSE](LICENSE) 文件。
