"""Built-in plugins for the multibot system."""

from src.plugins.builtin.error_handler import ErrorHandlerPlugin
from src.plugins.builtin.help import HelpPlugin
from src.plugins.builtin.start import StartPlugin

__all__ = ["StartPlugin", "HelpPlugin", "ErrorHandlerPlugin"]
