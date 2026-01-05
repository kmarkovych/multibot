# Telegram Multibot System

A production-ready system for running multiple Telegram bots within a single container using Python 3.11+, aiogram 3.x, and PostgreSQL.

## Features

- **Multi-bot Management**: Run multiple Telegram bots from a single process
- **Plugin Architecture**: Modular plugin system with shared base functionality
- **Hot Reload**: Update bot configs and plugins without restarting
- **Admin Bot**: Control all bots via Telegram (start/stop/reload/status)
- **Dual Mode**: Support both polling and webhook modes per bot
- **Health Checks**: HTTP endpoints for Kubernetes/monitoring
- **Rate Limiting**: Per-user rate limiting with token bucket algorithm
- **Structured Logging**: JSON logging for production environments
- **Docker Ready**: Multi-stage Dockerfile and Docker Compose setup

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Creating Bots](#creating-bots)
- [Creating Plugins](#creating-plugins)
- [Admin Bot Commands](#admin-bot-commands)
- [Docker Deployment](#docker-deployment)
- [API Reference](#api-reference)
- [Architecture](#architecture)

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

### Installation

```bash
# Clone the repository
cd multibot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
```

### Configuration

Edit `.env` with your values:

```bash
# Required: Database
DATABASE_URL=postgresql://multibot:password@localhost:5432/multibot

# Required: Admin bot
ADMIN_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_ALLOWED_USERS=123456789  # Your Telegram user ID

# Optional: Your bot tokens
BOT_MYBOT_TOKEN=987654321:ZYXwvuTSRqponMLKjihGFEdcba
```

### Create Your First Bot

Create `config/bots/mybot.yaml`:

```yaml
id: "mybot"
name: "My First Bot"
token: "${BOT_MYBOT_TOKEN}"
enabled: true
mode: "polling"

plugins:
  - name: "start"
    config:
      welcome_message: "Hello! Welcome to my bot!"
  - name: "help"
  - name: "error_handler"
```

### Run

```bash
# Start PostgreSQL (if not running)
docker run -d --name postgres \
  -e POSTGRES_USER=multibot \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=multibot \
  -p 5432:5432 \
  postgres:15-alpine

# Run migrations
cd migrations && alembic upgrade head && cd ..

# Start the system
python -m src.main
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `ADMIN_BOT_TOKEN` | Token for the admin control bot | Required |
| `ADMIN_ALLOWED_USERS` | Comma-separated admin user IDs | Required |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `LOG_FORMAT` | Log format (`json` or `text`) | `json` |
| `HEALTH_CHECK_ENABLED` | Enable health endpoints | `true` |
| `HEALTH_CHECK_PORT` | Health server port | `8080` |
| `WEBHOOK_ENABLED` | Enable webhook server | `false` |
| `WEBHOOK_BASE_URL` | Public URL for webhooks | - |
| `WEBHOOK_PORT` | Webhook server port | `8443` |
| `ENABLE_HOT_RELOAD` | Watch for config changes | `true` |
| `CONFIG_DIR` | Bot config directory | `./config/bots` |
| `PLUGINS_DIR` | Custom plugins directory | `./src/plugins/custom` |

### Bot Configuration (YAML)

Each bot is configured via a YAML file in `config/bots/`:

```yaml
# Bot identification
id: "support_bot"           # Unique identifier (required)
name: "Support Bot"         # Display name (required)
description: "Customer support bot"
token: "${BOT_TOKEN}"       # Token or env var reference (required)
enabled: true               # Whether to start this bot

# Operating mode
mode: "polling"             # "polling" or "webhook"

# Webhook settings (only for webhook mode)
webhook:
  path: "/support"          # Webhook path suffix
  max_connections: 40

# Bot settings passed to aiogram
settings:
  parse_mode: "HTML"        # Default parse mode
  disable_web_page_preview: false

# Plugins to load (order matters)
plugins:
  - name: "start"
    enabled: true
    config:
      welcome_message: "Welcome to Support!"

  - name: "help"
    config:
      header: "Available Commands"
      commands:
        - command: "/start"
          description: "Start the bot"
        - command: "/help"
          description: "Show help"
        - command: "/ticket"
          description: "Create support ticket"

  - name: "error_handler"
    config:
      show_error_id: true
      notify_admins: false

# Access control
access:
  allowed_users: []         # Empty = allow all
  blocked_users: []         # Blocked user IDs
  admin_users:              # Bot-specific admins
    - 123456789

# Rate limiting
rate_limiting:
  enabled: true
  default_rate: 30          # Requests per minute
  burst_size: 10

# FSM storage strategy
fsm_strategy: "USER_IN_CHAT"  # GLOBAL_USER, USER_IN_CHAT, CHAT
```

---

## Creating Bots

### Step 1: Get a Bot Token

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the token (e.g., `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Add Token to Environment

Add to `.env`:
```bash
BOT_MYBOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### Step 3: Create Bot Configuration

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
      welcome_message: |
        Welcome to My Bot!

        Use /help to see available commands.
  - name: "help"
  - name: "error_handler"
```

### Step 4: Start or Reload

If the system is running with hot reload enabled, the bot will start automatically. Otherwise, restart the system or use the admin bot:

```
/reload mybot
```

---

## Creating Plugins

Plugins are the building blocks for bot functionality. Each plugin can define command handlers, message handlers, callback handlers, and more.

### Plugin Structure

Create a new file in `src/plugins/custom/` or `src/plugins/builtin/`:

```python
# src/plugins/custom/echo.py

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.plugins.base import BasePlugin


class EchoPlugin(BasePlugin):
    """A simple echo plugin that repeats user messages."""

    # Plugin metadata
    name = "echo"
    description = "Echoes user messages back"
    version = "1.0.0"
    author = "Your Name"

    # Dependencies (loaded first)
    dependencies = set()  # e.g., {"start", "help"}

    # Hot reload support
    supports_hot_reload = True

    def setup_handlers(self, router: Router) -> None:
        """Register all handlers for this plugin."""

        @router.message(Command("echo"))
        async def cmd_echo(message: Message) -> None:
            """Handle /echo command."""
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                await message.answer(args[1])
            else:
                await message.answer("Usage: /echo <text>")

        @router.message()
        async def echo_all(message: Message) -> None:
            """Echo all text messages (if enabled in config)."""
            if self.get_config("echo_all", False) and message.text:
                await message.answer(f"You said: {message.text}")

    async def on_load(self, bot) -> None:
        """Called when plugin is loaded."""
        print(f"Echo plugin loaded for bot {self._bot_id}")

    async def on_unload(self, bot) -> None:
        """Called when plugin is unloaded."""
        print(f"Echo plugin unloaded from bot {self._bot_id}")


# Export for auto-discovery
plugin = EchoPlugin
```

### Using Your Plugin

Add it to your bot's config:

```yaml
plugins:
  - name: "echo"
    enabled: true
    config:
      echo_all: false  # Set to true to echo all messages
```

### Plugin Lifecycle Hooks

```python
class MyPlugin(BasePlugin):

    async def on_load(self, bot: Bot) -> None:
        """Called when plugin is loaded for a bot."""
        # Initialize resources, load data from DB, etc.
        pass

    async def on_unload(self, bot: Bot) -> None:
        """Called when plugin is unloaded."""
        # Cleanup resources, save state, etc.
        pass

    async def on_bot_start(self, bot: Bot) -> None:
        """Called when the bot starts polling/webhook."""
        # Send startup notifications, etc.
        pass

    async def on_bot_stop(self, bot: Bot) -> None:
        """Called when the bot stops."""
        # Send shutdown notifications, etc.
        pass
```

### Accessing Plugin Configuration

```python
def setup_handlers(self, router: Router) -> None:

    @router.message(Command("greet"))
    async def greet(message: Message) -> None:
        # Get config with default value
        greeting = self.get_config("greeting", "Hello!")
        name = self.get_config("name", "User")

        await message.answer(f"{greeting}, {name}!")
```

### Accessing Database

```python
from src.database.repositories.bot_repository import UserRepository

class MyPlugin(BasePlugin):

    def setup_handlers(self, router: Router) -> None:

        @router.message(Command("stats"))
        async def stats(message: Message, session) -> None:
            """Show user stats. Session is injected by middleware."""
            repo = UserRepository(session)
            count = await repo.get_user_count(self._bot_id)
            await message.answer(f"Total users: {count}")
```

### Using Finite State Machine (FSM)

```python
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from src.plugins.base import BasePlugin


class Form(StatesGroup):
    """States for the form."""
    waiting_for_name = State()
    waiting_for_age = State()


class FormPlugin(BasePlugin):
    name = "form"
    description = "Multi-step form example"
    version = "1.0.0"

    def setup_handlers(self, router: Router) -> None:

        @router.message(Command("form"))
        async def start_form(message: Message, state: FSMContext) -> None:
            await state.set_state(Form.waiting_for_name)
            await message.answer("What's your name?")

        @router.message(Form.waiting_for_name)
        async def process_name(message: Message, state: FSMContext) -> None:
            await state.update_data(name=message.text)
            await state.set_state(Form.waiting_for_age)
            await message.answer("How old are you?")

        @router.message(Form.waiting_for_age)
        async def process_age(message: Message, state: FSMContext) -> None:
            data = await state.get_data()
            name = data.get("name")
            age = message.text

            await state.clear()
            await message.answer(f"Hello {name}, you are {age} years old!")


plugin = FormPlugin
```

### Inline Keyboards

```python
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.plugins.base import BasePlugin


class MenuPlugin(BasePlugin):
    name = "menu"
    description = "Interactive menu example"
    version = "1.0.0"

    def setup_handlers(self, router: Router) -> None:

        @router.message(Command("menu"))
        async def show_menu(message: Message) -> None:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="Option 1", callback_data="opt_1"),
                    InlineKeyboardButton(text="Option 2", callback_data="opt_2"),
                ],
                [
                    InlineKeyboardButton(text="Cancel", callback_data="cancel"),
                ],
            ])
            await message.answer("Choose an option:", reply_markup=keyboard)

        @router.callback_query(F.data.startswith("opt_"))
        async def handle_option(callback: CallbackQuery) -> None:
            option = callback.data.split("_")[1]
            await callback.answer(f"You selected option {option}")
            await callback.message.edit_text(f"Selected: Option {option}")

        @router.callback_query(F.data == "cancel")
        async def handle_cancel(callback: CallbackQuery) -> None:
            await callback.answer("Cancelled")
            await callback.message.delete()


plugin = MenuPlugin
```

---

## Admin Bot Commands

The admin bot allows you to control all other bots via Telegram.

### Status & Monitoring

| Command | Description |
|---------|-------------|
| `/status` | Show status of all bots |
| `/status <bot_id>` | Show detailed status for a specific bot |
| `/list` | List all configured bots |
| `/health` | Show system health status |

### Bot Control

| Command | Description |
|---------|-------------|
| `/start_bot <bot_id>` | Start a stopped bot |
| `/stop_bot <bot_id>` | Stop a running bot |
| `/restart_bot <bot_id>` | Restart a bot |

### Configuration

| Command | Description |
|---------|-------------|
| `/reload <bot_id>` | Reload a bot's configuration |
| `/reload_all` | Reload all bot configurations |

### Example Usage

```
You: /status

Admin Bot:
📊 Bot Status Overview

✅ support_bot (Support Bot) - 2h 34m
✅ notification_bot (Notifications) - 2h 34m
⏹️ test_bot (Test Bot)

Summary: 2/3 running

You: /start_bot test_bot

Admin Bot:
Start bot Test Bot (test_bot)?
[✅ Confirm] [❌ Cancel]

You: [clicks Confirm]

Admin Bot:
✅ Bot test_bot started successfully
```

---

## Docker Deployment

### Quick Start with Docker Compose

```bash
cd docker

# Create .env file in project root
cp ../.env.example ../.env
# Edit ../.env with your values

# Start all services
docker compose up -d

# View logs
docker compose logs -f multibot

# Stop
docker compose down
```

### Docker Compose Services

- **multibot**: The main application
- **postgres**: PostgreSQL database
- **redis**: Redis for FSM storage (optional)

### Production Configuration

Create `docker/docker-compose.prod.yml`:

```yaml
services:
  multibot:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G

  postgres:
    ports: []  # Don't expose in production
```

Run with:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Health Checks

The system exposes health check endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /health/live` | Liveness probe (is process alive?) |
| `GET /health/ready` | Readiness probe (can accept traffic?) |
| `GET /health/full` | Detailed health information |
| `GET /metrics` | Prometheus-compatible metrics |

---

## API Reference

### BasePlugin

```python
class BasePlugin(ABC):
    # Metadata
    name: str                    # Plugin identifier (required)
    description: str             # Human-readable description
    version: str                 # Semantic version
    author: str                  # Author name

    # Dependencies
    dependencies: set[str]       # Plugin names to load first
    supports_hot_reload: bool    # Can be reloaded at runtime

    # Methods
    def setup_handlers(self, router: Router) -> None:
        """Register handlers (required)."""

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""

    async def on_load(self, bot: Bot) -> None:
        """Called when loaded."""

    async def on_unload(self, bot: Bot) -> None:
        """Called when unloaded."""

    async def on_bot_start(self, bot: Bot) -> None:
        """Called when bot starts."""

    async def on_bot_stop(self, bot: Bot) -> None:
        """Called when bot stops."""

    # Properties
    @property
    def bot_id(self) -> str:
        """Current bot ID."""

    @property
    def db(self) -> DatabaseManager:
        """Database manager."""
```

### Configuration Models

```python
from src.core.config import (
    AppConfig,      # Application configuration
    BotConfig,      # Bot configuration
    PluginConfig,   # Plugin configuration
    ConfigManager,  # Config loading and management
)
```

### Database Models

```python
from src.database.models import (
    BotRecord,      # Bot configuration and state
    BotUser,        # Users who interacted with bots
    BotEvent,       # Audit log of events
    PluginState,    # Plugin persistent state
)
```

### Repositories

```python
from src.database.repositories.bot_repository import (
    BotRepository,          # Bot CRUD operations
    UserRepository,         # User operations
    PluginStateRepository,  # Plugin state storage
)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MultibotApplication                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    BotManager                        │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │    │
│  │  │ Bot 1   │  │ Bot 2   │  │ Bot N   │             │    │
│  │  │Dispatcher│  │Dispatcher│  │Dispatcher│             │    │
│  │  │ Plugins │  │ Plugins │  │ Plugins │             │    │
│  │  └─────────┘  └─────────┘  └─────────┘             │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │HealthServer │  │WebhookServer │  │ConfigWatcher │      │
│  │  :8080      │  │  :8443       │  │ (hot reload) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │PluginRegistry│  │DatabaseManager│                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  PostgreSQL  │
                    └──────────────┘
```

---

## Troubleshooting

### Bot not starting

1. Check the token is correct in `.env`
2. Check the YAML config is valid: `python -c "import yaml; yaml.safe_load(open('config/bots/mybot.yaml'))"`
3. Check logs: `docker compose logs multibot`

### Plugin not loading

1. Ensure the file is in `src/plugins/custom/` or `src/plugins/builtin/`
2. Check the file has `plugin = YourPluginClass` at the bottom
3. Verify the plugin name in config matches the class `name` attribute

### Database connection failed

1. Ensure PostgreSQL is running
2. Check `DATABASE_URL` format: `postgresql://user:pass@host:5432/dbname`
3. Run migrations: `cd migrations && alembic upgrade head`

### Hot reload not working

1. Ensure `ENABLE_HOT_RELOAD=true`
2. Check the config directory path is correct
3. File changes take 1-2 seconds to be detected

---

## License

MIT License
