# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run the application
python -m src.main

# Run database migrations
cd migrations && alembic upgrade head && cd ..

# Linting
ruff check src/ tests/

# Run all tests
pytest tests/ -v

# Run single test file
pytest tests/unit/test_config.py -v

# Run single test
pytest tests/unit/test_config.py::test_bot_config_loading -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html
```

## Architecture Overview

This is a **multi-bot Telegram system** using aiogram 3.x with a plugin-based architecture.

### Core Flow

```
MultibotApplication (src/core/app.py)
    → BotManager (src/core/bot_manager.py)
        → ManagedBot instances
            → Bot (aiogram) + Dispatcher + Plugins
```

### Key Components

**BotManager** (`src/core/bot_manager.py`): Manages bot lifecycle (create, start, stop, reload). Each bot runs as an asyncio task in polling mode. Stores `ManagedBot` dataclass instances tracking state and loaded plugins.

**DispatcherFactory** (`src/core/dispatcher_factory.py`): Creates aiogram Dispatcher with:
- FSM storage (MemoryStorage)
- Plugin routers (resolved by dependency order)
- Middleware stack (logging → database → rate limit)

**PluginRegistry** (`src/plugins/registry.py`): Central registry for plugins. Handles:
- Built-in plugin loading (`load_builtin_plugins()`)
- Custom plugin discovery from directories
- Dependency resolution with topological sort

**ConfigManager** (`src/core/config.py`): Loads YAML bot configs from `config/bots/`. Supports `${ENV_VAR}` syntax for environment variable substitution.

### Plugin System

Plugins extend `BasePlugin` (`src/plugins/base.py`):
- Define `name`, `description`, `version`, `dependencies`
- Implement `setup_handlers(router)` to register aiogram handlers
- Lifecycle hooks: `on_load()`, `on_unload()`, `on_bot_start()`, `on_bot_stop()`
- Access config via `self.get_config(key, default)`
- Access database via `self.db` (DatabaseManager)

Plugin locations:
- Built-in: `src/plugins/builtin/` (start, help, error_handler)
- Custom: `src/plugins/custom/` (single .py files or packages with `__init__.py`)

Plugin discovery: Both `.py` files and directories with `__init__.py` are scanned. Export plugin class as `plugin = YourPlugin`.

### Database

PostgreSQL with SQLAlchemy async ORM. Models in `src/database/models.py`:
- `BotRecord`: Bot configurations
- `BotUser`: Users interacting with bots
- `BotEvent`: Audit events
- `PluginState`: Key-value storage for plugins (use `PluginStateRepository`)

### Middleware Stack

Defined in `src/middleware/`:
1. `LoggingMiddleware`: Request ID generation, timing
2. `DatabaseMiddleware`: Injects AsyncSession into handler
3. `RateLimitMiddleware`: Token bucket per-user limiting

### Configuration

Environment: `.env` file loaded by python-dotenv
Bot configs: YAML files in `config/bots/` with structure:
```yaml
id: "bot_id"
name: "Bot Name"
token: "${BOT_TOKEN}"  # env var reference
enabled: true
mode: "polling"  # or "webhook"
plugins:
  - name: "plugin_name"
    enabled: true
    config: {...}
```

### Hot Reload

When `ENABLE_HOT_RELOAD=true`, `ConfigWatcher` (`src/utils/watcher.py`) monitors config and plugin files. Changes trigger bot reload via `BotManager.reload_bot()`.

## Code Quality

- Ruff linter with rules: E, F, I, UP, B, SIM
- Target Python 3.11+
- Line length: 100
- Type annotations with `from __future__ import annotations`
- Use TYPE_CHECKING imports for type hints that would cause circular imports
- Do not mention Claude in commit messages
