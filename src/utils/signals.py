"""Signal handling for graceful shutdown."""

from __future__ import annotations

import asyncio
import logging
import signal
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)


class SignalHandler:
    """
    Handles Unix signals for graceful shutdown.

    Supports:
    - SIGTERM: Graceful shutdown
    - SIGINT: Graceful shutdown (Ctrl+C)
    - SIGHUP: Reload configuration
    """

    def __init__(self):
        self._shutdown_event = asyncio.Event()
        self._reload_callbacks: list[Callable[[], Awaitable[None]]] = []
        self._shutdown_callbacks: list[Callable[[], Awaitable[None]]] = []

    def setup(self) -> None:
        """Setup signal handlers."""
        loop = asyncio.get_event_loop()

        # Handle SIGTERM and SIGINT for shutdown
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self._handle_shutdown(s)),
            )

        # Handle SIGHUP for reload
        loop.add_signal_handler(
            signal.SIGHUP,
            lambda: asyncio.create_task(self._handle_reload()),
        )

        logger.info("Signal handlers configured")

    async def _handle_shutdown(self, sig: signal.Signals) -> None:
        """Handle shutdown signal."""
        logger.info(f"Received signal {sig.name}, initiating shutdown...")
        self._shutdown_event.set()

        # Run shutdown callbacks
        for callback in self._shutdown_callbacks:
            try:
                await callback()
            except Exception as e:
                logger.error(f"Error in shutdown callback: {e}")

    async def _handle_reload(self) -> None:
        """Handle reload signal (SIGHUP)."""
        logger.info("Received SIGHUP, reloading configuration...")

        for callback in self._reload_callbacks:
            try:
                await callback()
            except Exception as e:
                logger.error(f"Error in reload callback: {e}")

        logger.info("Configuration reload complete")

    def on_shutdown(self, callback: Callable[[], Awaitable[None]]) -> None:
        """Register a callback to be called on shutdown."""
        self._shutdown_callbacks.append(callback)

    def on_reload(self, callback: Callable[[], Awaitable[None]]) -> None:
        """Register a callback to be called on SIGHUP."""
        self._reload_callbacks.append(callback)

    async def wait_for_shutdown(self) -> None:
        """Wait until shutdown is requested."""
        await self._shutdown_event.wait()

    @property
    def is_shutting_down(self) -> bool:
        """Check if shutdown has been requested."""
        return self._shutdown_event.is_set()
