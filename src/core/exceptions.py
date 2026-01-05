"""Custom exceptions for the multibot system."""


class MultibotError(Exception):
    """Base exception for multibot system."""

    pass


class BotNotFoundError(MultibotError):
    """Raised when a bot ID is not found."""

    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        super().__init__(f"Bot not found: {bot_id}")


class BotAlreadyRunningError(MultibotError):
    """Raised when trying to start an already running bot."""

    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        super().__init__(f"Bot is already running: {bot_id}")


class BotNotRunningError(MultibotError):
    """Raised when trying to stop a bot that is not running."""

    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        super().__init__(f"Bot is not running: {bot_id}")


class PluginLoadError(MultibotError):
    """Raised when a plugin fails to load."""

    def __init__(self, plugin_name: str, reason: str):
        self.plugin_name = plugin_name
        self.reason = reason
        super().__init__(f"Failed to load plugin '{plugin_name}': {reason}")


class PluginNotFoundError(MultibotError):
    """Raised when a plugin is not found."""

    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        super().__init__(f"Plugin not found: {plugin_name}")


class ConfigValidationError(MultibotError):
    """Raised when configuration validation fails."""

    def __init__(self, message: str, errors: list | None = None):
        self.errors = errors or []
        super().__init__(message)


class ConfigFileNotFoundError(MultibotError):
    """Raised when a configuration file is not found."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Configuration file not found: {path}")
