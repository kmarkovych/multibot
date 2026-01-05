"""Built-in plugins for the multibot system."""

from src.plugins.builtin.start import StartPlugin
from src.plugins.builtin.help import HelpPlugin
from src.plugins.builtin.error_handler import ErrorHandlerPlugin

__all__ = ["StartPlugin", "HelpPlugin", "ErrorHandlerPlugin"]
