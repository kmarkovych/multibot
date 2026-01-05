"""File watcher for hot reload functionality."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

from watchfiles import Change, awatch

logger = logging.getLogger(__name__)


class ConfigWatcher:
    """
    Watches configuration files and plugin directories for changes.

    Uses watchfiles (Rust-based) for efficient file watching.
    Debounces changes to avoid rapid reloading.
    """

    def __init__(
        self,
        watch_paths: list[str | Path],
        on_config_change: Callable[[str, Path], Awaitable[None]],
        on_plugin_change: Callable[[str, Path], Awaitable[None]],
        debounce_ms: int = 1600,
    ):
        self.watch_paths = [Path(p) for p in watch_paths if Path(p).exists()]
        self.on_config_change = on_config_change
        self.on_plugin_change = on_plugin_change
        self.debounce_ms = debounce_ms
        self._stop_event = asyncio.Event()
        self._watch_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start watching for file changes."""
        if not self.watch_paths:
            logger.warning("No valid paths to watch")
            return

        self._watch_task = asyncio.create_task(self._watch_loop())
        logger.info(f"Started watching paths: {self.watch_paths}")

    async def stop(self) -> None:
        """Stop watching."""
        self._stop_event.set()
        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
            self._watch_task = None
        logger.info("Config watcher stopped")

    async def _watch_loop(self) -> None:
        """Main watch loop using watchfiles."""
        try:
            async for changes in awatch(
                *self.watch_paths,
                stop_event=self._stop_event,
                debounce=self.debounce_ms,
                recursive=True,
            ):
                await self._handle_changes(changes)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in watch loop: {e}")

    async def _handle_changes(self, changes: set[tuple[Change, str]]) -> None:
        """Process file changes."""
        for change_type, path_str in changes:
            path = Path(path_str)

            # Ignore hidden files and temp files
            if path.name.startswith(".") or path.name.endswith("~"):
                continue

            # Determine change type
            change_name = {
                Change.added: "added",
                Change.modified: "modified",
                Change.deleted: "deleted",
            }.get(change_type, "unknown")

            logger.debug(f"File {change_name}: {path}")

            # Route to appropriate handler
            if path.suffix in (".yaml", ".yml"):
                await self._handle_config_change(change_name, path)
            elif path.suffix == ".py":
                await self._handle_plugin_change(change_name, path)

    async def _handle_config_change(self, change_type: str, path: Path) -> None:
        """Handle bot configuration file changes."""
        if change_type == "deleted":
            logger.info(f"Config file deleted: {path}")
            return

        try:
            # Extract bot_id from filename (e.g., support_bot.yaml -> support_bot)
            bot_id = path.stem

            logger.info(f"Config change detected for bot: {bot_id}")
            await self.on_config_change(bot_id, path)

        except Exception as e:
            logger.error(f"Error handling config change: {e}")

    async def _handle_plugin_change(self, change_type: str, path: Path) -> None:
        """Handle plugin file changes."""
        # Skip __init__.py and other special files
        if path.name.startswith("_"):
            return

        if change_type == "deleted":
            logger.info(f"Plugin file deleted: {path}")
            return

        try:
            # Extract plugin name from path
            plugin_name = path.stem

            logger.info(f"Plugin change detected: {plugin_name}")
            await self.on_plugin_change(plugin_name, path)

        except Exception as e:
            logger.error(f"Error handling plugin change: {e}")
