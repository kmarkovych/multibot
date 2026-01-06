"""Configuration management for the multibot system."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def resolve_env_vars(value: Any) -> Any:
    """Recursively resolve ${VAR_NAME} environment variable references."""
    if isinstance(value, str):
        pattern = r"\$\{([^}]+)\}"
        matches = re.findall(pattern, value)
        result = value
        for match in matches:
            env_value = os.getenv(match, "")
            result = result.replace(f"${{{match}}}", env_value)
        return result
    elif isinstance(value, dict):
        return {k: resolve_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [resolve_env_vars(item) for item in value]
    return value


class DatabaseConfig(BaseModel):
    """Database configuration."""

    url: str = Field(default="postgresql://localhost:5432/multibot")
    pool_size: int = Field(default=10, ge=1, le=100)
    pool_max_overflow: int = Field(default=20, ge=0, le=100)
    pool_recycle: int = Field(default=3600, ge=60)
    pool_timeout: int = Field(default=30, ge=5)


class HealthConfig(BaseModel):
    """Health check server configuration."""

    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = Field(default=8080, ge=1, le=65535)
    liveness_path: str = "/health/live"
    readiness_path: str = "/health/ready"


class WebhookConfig(BaseModel):
    """Webhook server configuration."""

    enabled: bool = False
    base_url: str = ""
    host: str = "0.0.0.0"
    port: int = Field(default=8443, ge=1, le=65535)
    secret: str = ""
    path_prefix: str = "/webhook"


class HotReloadConfig(BaseModel):
    """Hot reload configuration."""

    enabled: bool = True
    watch_interval: int = Field(default=5, ge=1)
    debounce_ms: int = Field(default=1600, ge=100)


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    enabled: bool = True
    default_rate: int = Field(default=30, ge=1)  # requests per minute
    burst_size: int = Field(default=10, ge=1)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    format: Literal["json", "text"] = "json"
    include_request_id: bool = True


class PluginConfig(BaseModel):
    """Configuration for a single plugin."""

    name: str
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class AccessConfig(BaseModel):
    """Access control configuration for a bot."""

    allowed_users: list[int] = Field(default_factory=list)
    blocked_users: list[int] = Field(default_factory=list)
    admin_users: list[int] = Field(default_factory=list)


class BotWebhookConfig(BaseModel):
    """Per-bot webhook configuration."""

    path: str = ""
    secret: str | None = None
    max_connections: int = Field(default=40, ge=1, le=100)


class BotConfig(BaseModel):
    """Configuration for a single bot."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    token: str = ""  # Empty token = bot will be skipped
    enabled: bool = True
    mode: Literal["polling", "webhook"] = "polling"
    webhook: BotWebhookConfig = Field(default_factory=BotWebhookConfig)
    settings: dict[str, Any] = Field(default_factory=dict)
    plugins: list[PluginConfig] = Field(default_factory=list)
    access: AccessConfig = Field(default_factory=AccessConfig)
    rate_limiting: RateLimitConfig | None = None
    fsm_strategy: str = "USER_IN_CHAT"

    @field_validator("token", mode="before")
    @classmethod
    def resolve_token_env(cls, v: Any) -> str:
        """Resolve environment variable references in token."""
        return resolve_env_vars(v)

    @model_validator(mode="before")
    @classmethod
    def resolve_all_env_vars(cls, data: Any) -> Any:
        """Resolve all environment variable references."""
        if isinstance(data, dict):
            return resolve_env_vars(data)
        return data


class AppConfig(BaseSettings):
    """Main application configuration loaded from environment."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="postgresql://multibot:password@localhost:5432/multibot",
        alias="DATABASE_URL",
    )
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    database_pool_max_overflow: int = Field(default=20, alias="DATABASE_POOL_MAX_OVERFLOW")

    # Admin bot
    admin_bot_token: str = Field(default="", alias="ADMIN_BOT_TOKEN")
    admin_allowed_users: str = Field(default="", alias="ADMIN_ALLOWED_USERS")

    # Health checks
    health_check_enabled: bool = Field(default=True, alias="HEALTH_CHECK_ENABLED")
    health_check_host: str = Field(default="0.0.0.0", alias="HEALTH_CHECK_HOST")
    health_check_port: int = Field(default=8080, alias="HEALTH_CHECK_PORT")

    # Webhook
    webhook_enabled: bool = Field(default=False, alias="WEBHOOK_ENABLED")
    webhook_base_url: str = Field(default="", alias="WEBHOOK_BASE_URL")
    webhook_host: str = Field(default="0.0.0.0", alias="WEBHOOK_HOST")
    webhook_port: int = Field(default=8443, alias="WEBHOOK_PORT")
    webhook_secret: str = Field(default="", alias="WEBHOOK_SECRET")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # Hot reload
    hot_reload_enabled: bool = Field(default=True, alias="ENABLE_HOT_RELOAD")
    config_dir: str = Field(default="/app/config/bots", alias="CONFIG_DIR")
    plugins_dir: str = Field(default="/app/src/plugins/custom", alias="PLUGINS_DIR")

    @property
    def database(self) -> DatabaseConfig:
        """Get database configuration."""
        return DatabaseConfig(
            url=self.database_url,
            pool_size=self.database_pool_size,
            pool_max_overflow=self.database_pool_max_overflow,
        )

    @property
    def health(self) -> HealthConfig:
        """Get health check configuration."""
        return HealthConfig(
            enabled=self.health_check_enabled,
            host=self.health_check_host,
            port=self.health_check_port,
        )

    @property
    def webhook(self) -> WebhookConfig:
        """Get webhook configuration."""
        return WebhookConfig(
            enabled=self.webhook_enabled,
            base_url=self.webhook_base_url,
            host=self.webhook_host,
            port=self.webhook_port,
            secret=self.webhook_secret,
        )

    @property
    def hot_reload(self) -> HotReloadConfig:
        """Get hot reload configuration."""
        return HotReloadConfig(enabled=self.hot_reload_enabled)

    @property
    def logging(self) -> LoggingConfig:
        """Get logging configuration."""
        return LoggingConfig(
            level=self.log_level.upper(),  # type: ignore
            format=self.log_format.lower(),  # type: ignore
        )

    @property
    def admin_user_ids(self) -> list[int]:
        """Parse admin allowed users from comma-separated string."""
        if not self.admin_allowed_users:
            return []
        return [int(uid.strip()) for uid in self.admin_allowed_users.split(",") if uid.strip()]


class ConfigManager:
    """Manages configuration loading and validation."""

    def __init__(self, app_config: AppConfig):
        self.app_config = app_config
        self._bot_configs: dict[str, BotConfig] = {}

    @classmethod
    def load_from_env(cls) -> ConfigManager:
        """Load application configuration from environment."""
        app_config = AppConfig()
        return cls(app_config)

    def load_bot_configs(self, config_dir: Path | str | None = None) -> dict[str, BotConfig]:
        """Load all bot configurations from YAML files."""
        if config_dir is None:
            config_dir = Path(self.app_config.config_dir)
        else:
            config_dir = Path(config_dir)

        self._bot_configs.clear()

        if not config_dir.exists():
            return self._bot_configs

        for config_file in config_dir.glob("*.yaml"):
            self._load_and_register_bot(config_file)

        for config_file in config_dir.glob("*.yml"):
            self._load_and_register_bot(config_file)

        return self._bot_configs

    def _load_and_register_bot(self, config_file: Path) -> None:
        """Load a bot config and register it if valid."""
        try:
            # Read raw config to get original token reference
            with open(config_file) as f:
                raw_config = yaml.safe_load(f)
            raw_token = raw_config.get("token", "")

            bot_config = self.load_bot_config(config_file)

            # Skip bots with missing tokens
            if not bot_config.token:
                # Extract env var name from ${VAR_NAME} pattern
                env_var_match = re.search(r"\$\{([^}]+)\}", raw_token)
                env_var_hint = f" (set {env_var_match.group(1)} env var)" if env_var_match else ""
                print(f"Skipping {config_file.name}: token not configured{env_var_hint}")
                return

            # Skip disabled bots
            if not bot_config.enabled:
                print(f"Skipping {config_file.name}: bot is disabled")
                return

            self._bot_configs[bot_config.id] = bot_config
            print(f"Loaded bot config: {bot_config.id} ({bot_config.name})")

        except Exception as e:
            # Log error but continue loading other configs
            print(f"Error loading config {config_file}: {e}")

    def load_bot_config(self, config_path: Path | str) -> BotConfig:
        """Load a single bot configuration from a YAML file."""
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path) as f:
            raw_config = yaml.safe_load(f)

        # Resolve environment variables
        resolved_config = resolve_env_vars(raw_config)

        return BotConfig.model_validate(resolved_config)

    def get_bot_config(self, bot_id: str) -> BotConfig | None:
        """Get a bot configuration by ID."""
        return self._bot_configs.get(bot_id)

    def reload_bot_config(self, bot_id: str) -> BotConfig | None:
        """Reload a specific bot's configuration from disk."""
        config_dir = Path(self.app_config.config_dir)

        for ext in [".yaml", ".yml"]:
            config_path = config_dir / f"{bot_id}{ext}"
            if config_path.exists():
                bot_config = self.load_bot_config(config_path)
                self._bot_configs[bot_id] = bot_config
                return bot_config

        return None

    @property
    def bot_configs(self) -> dict[str, BotConfig]:
        """Get all loaded bot configurations."""
        return self._bot_configs.copy()
