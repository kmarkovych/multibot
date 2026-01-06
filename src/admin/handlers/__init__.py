"""Admin command handlers."""

from src.admin.handlers.bot_control import router as bot_control_router
from src.admin.handlers.stats import router as stats_router
from src.admin.handlers.status import router as status_router

__all__ = ["status_router", "bot_control_router", "stats_router"]
