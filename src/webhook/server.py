"""Webhook server for handling Telegram updates."""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import TYPE_CHECKING

from aiogram.types import Update
from aiohttp import web

if TYPE_CHECKING:
    from src.core.bot_manager import BotManager

logger = logging.getLogger(__name__)


class WebhookServer:
    """
    HTTP server for handling Telegram webhook updates.

    Each bot gets its own webhook path based on its ID.
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8443,
        bot_manager: BotManager | None = None,
        base_url: str = "",
        secret: str = "",
        path_prefix: str = "/webhook",
    ):
        self.host = host
        self.port = port
        self.bot_manager = bot_manager
        self.base_url = base_url
        self.secret = secret
        self.path_prefix = path_prefix
        self.app = web.Application()
        self._runner: web.AppRunner | None = None
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup webhook routes."""
        # Dynamic route for bot webhooks: /webhook/{bot_id}
        self.app.router.add_post(
            f"{self.path_prefix}/{{bot_id}}",
            self._webhook_handler,
        )

    def _verify_secret(self, request: web.Request, bot_id: str) -> bool:
        """Verify the webhook secret token."""
        if not self.secret:
            return True

        # Telegram sends the secret in X-Telegram-Bot-Api-Secret-Token header
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")

        # Compare with expected secret (can be per-bot or global)
        expected = self._get_bot_secret(bot_id)

        return hmac.compare_digest(token, expected)

    def _get_bot_secret(self, bot_id: str) -> str:
        """Get the secret token for a specific bot."""
        if not self.secret:
            return ""

        # Create a per-bot secret by hashing the global secret with bot_id
        return hashlib.sha256(f"{self.secret}:{bot_id}".encode()).hexdigest()[:32]

    async def _webhook_handler(self, request: web.Request) -> web.Response:
        """Handle incoming webhook updates."""
        bot_id = request.match_info.get("bot_id")

        if not bot_id:
            return web.Response(status=400, text="Missing bot_id")

        if not self.bot_manager:
            return web.Response(status=503, text="Bot manager not available")

        managed_bot = self.bot_manager.get_bot(bot_id)
        if not managed_bot:
            logger.warning(f"Webhook received for unknown bot: {bot_id}")
            return web.Response(status=404, text="Bot not found")

        if managed_bot.state != "running":
            logger.warning(f"Webhook received for non-running bot: {bot_id}")
            return web.Response(status=503, text="Bot not running")

        # Verify secret
        if not self._verify_secret(request, bot_id):
            logger.warning(f"Invalid webhook secret for bot: {bot_id}")
            return web.Response(status=401, text="Unauthorized")

        try:
            # Parse the update
            data = await request.json()
            update = Update.model_validate(data)

            # Feed to dispatcher
            await managed_bot.dispatcher.feed_update(
                managed_bot.bot,
                update,
            )

            return web.Response(status=200, text="ok")

        except Exception as e:
            logger.error(f"Error processing webhook for {bot_id}: {e}")
            return web.Response(status=500, text="Internal error")

    def get_webhook_url(self, bot_id: str) -> str:
        """Get the webhook URL for a specific bot."""
        return f"{self.base_url}{self.path_prefix}/{bot_id}"

    async def setup_bot_webhook(self, bot_id: str) -> bool:
        """Set up webhook for a specific bot."""
        if not self.bot_manager:
            return False

        managed_bot = self.bot_manager.get_bot(bot_id)
        if not managed_bot:
            return False

        url = self.get_webhook_url(bot_id)
        secret = self._get_bot_secret(bot_id)

        try:
            await managed_bot.bot.set_webhook(
                url=url,
                secret_token=secret if secret else None,
                allowed_updates=managed_bot.dispatcher.resolve_used_update_types(),
            )
            logger.info(f"Webhook set for bot {bot_id}: {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to set webhook for bot {bot_id}: {e}")
            return False

    async def remove_bot_webhook(self, bot_id: str) -> bool:
        """Remove webhook for a specific bot."""
        if not self.bot_manager:
            return False

        managed_bot = self.bot_manager.get_bot(bot_id)
        if not managed_bot:
            return False

        try:
            await managed_bot.bot.delete_webhook()
            logger.info(f"Webhook removed for bot {bot_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove webhook for bot {bot_id}: {e}")
            return False

    async def start(self) -> None:
        """Start the webhook server."""
        self._runner = web.AppRunner(self.app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.host, self.port)
        await site.start()
        logger.info(f"Webhook server started on {self.host}:{self.port}")

        # Setup webhooks for all webhook-mode bots
        if self.bot_manager:
            for bot_id, managed_bot in self.bot_manager.get_all_bots().items():
                if managed_bot.mode == "webhook" and managed_bot.state == "running":
                    await self.setup_bot_webhook(bot_id)

    async def stop(self) -> None:
        """Stop the webhook server."""
        # Remove webhooks for all bots
        if self.bot_manager:
            for bot_id, managed_bot in self.bot_manager.get_all_bots().items():
                if managed_bot.mode == "webhook":
                    await self.remove_bot_webhook(bot_id)

        if self._runner:
            await self._runner.cleanup()
            self._runner = None
            logger.info("Webhook server stopped")
