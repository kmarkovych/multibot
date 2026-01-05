# Quick Start Guide

Get your first bot running in 5 minutes.

## 1. Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

## 2. Configure Your Bot

Edit `.env`:
```bash
# Database (use Docker or local PostgreSQL)
DATABASE_URL=postgresql://multibot:password@localhost:5432/multibot

# Admin bot (get token from @BotFather)
ADMIN_BOT_TOKEN=your_admin_bot_token
ADMIN_ALLOWED_USERS=your_telegram_user_id

# Your first bot
BOT_MYBOT_TOKEN=your_bot_token
```

## 3. Create Bot Config

Create `config/bots/mybot.yaml`:
```yaml
id: "mybot"
name: "My Bot"
token: "${BOT_MYBOT_TOKEN}"
enabled: true
mode: "polling"

plugins:
  - name: "start"
    config:
      welcome_message: "Hello! I'm your new bot!"
  - name: "help"
  - name: "error_handler"
```

## 4. Start Database

```bash
docker run -d --name postgres \
  -e POSTGRES_USER=multibot \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=multibot \
  -p 5432:5432 \
  postgres:15-alpine
```

## 5. Run Migrations

```bash
cd migrations
alembic upgrade head
cd ..
```

## 6. Start the System

```bash
python -m src.main
```

## 7. Test Your Bot

Open Telegram and send `/start` to your bot!

---

## Next Steps

- Add more plugins: See [Plugin Development](PLUGINS.md)
- Use Docker: See [Docker Deployment](../README.md#docker-deployment)
- Configure webhooks: See [Configuration](../README.md#configuration)
