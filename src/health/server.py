"""HTTP server for health check endpoints."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiohttp import web

from src.health.checks import check_bots, check_database, get_health_status

if TYPE_CHECKING:
    from src.core.bot_manager import BotManager
    from src.database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class HealthServer:
    """
    HTTP server for health check endpoints.

    Endpoints:
    - /health/live  - Liveness probe (is the process alive?)
    - /health/ready - Readiness probe (can it accept traffic?)
    - /health/full  - Detailed health information
    - /metrics      - Prometheus metrics
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        bot_manager: "BotManager | None" = None,
        db: "DatabaseManager | None" = None,
    ):
        self.host = host
        self.port = port
        self.bot_manager = bot_manager
        self.db = db
        self.app = web.Application()
        self._runner: web.AppRunner | None = None
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup HTTP routes."""
        self.app.router.add_get("/health/live", self._liveness_handler)
        self.app.router.add_get("/health/ready", self._readiness_handler)
        self.app.router.add_get("/health/full", self._full_health_handler)
        self.app.router.add_get("/metrics", self._metrics_handler)

    async def _liveness_handler(self, request: web.Request) -> web.Response:
        """
        Liveness probe - simple check that the process is running.

        Returns 200 if alive, used by Kubernetes to restart dead containers.
        """
        return web.json_response({"status": "alive"})

    async def _readiness_handler(self, request: web.Request) -> web.Response:
        """
        Readiness probe - check if the service can accept traffic.

        Checks:
        - Database connection is available
        - At least one bot is running
        """
        checks = {}
        is_ready = True

        # Check database
        if self.db:
            db_check = await check_database(self.db)
            checks["database"] = db_check["status"]
            if db_check["status"] != "healthy":
                is_ready = False

        # Check at least one bot is running
        if self.bot_manager:
            bots_check = await check_bots(self.bot_manager)
            checks["bots"] = f"{bots_check['running']}/{bots_check['total']} running"
            if bots_check["running"] == 0:
                is_ready = False

        status_code = 200 if is_ready else 503
        return web.json_response(
            {"status": "ready" if is_ready else "not_ready", "checks": checks},
            status=status_code,
        )

    async def _full_health_handler(self, request: web.Request) -> web.Response:
        """
        Full health check with detailed information.

        Returns comprehensive status of all components.
        """
        health = await get_health_status(self.bot_manager, self.db)

        # Add bot details
        if self.bot_manager:
            bots_detail = {}
            for bot_id, managed_bot in self.bot_manager.get_all_bots().items():
                bots_detail[bot_id] = {
                    "name": managed_bot.config.name,
                    "status": managed_bot.state,
                    "mode": managed_bot.mode,
                    "uptime_seconds": (
                        (
                            __import__("datetime").datetime.utcnow()
                            - managed_bot.started_at
                        ).total_seconds()
                        if managed_bot.started_at
                        else None
                    ),
                }
            health["bots"] = bots_detail

        return web.json_response(health)

    async def _metrics_handler(self, request: web.Request) -> web.Response:
        """Prometheus-compatible metrics endpoint."""
        metrics = []

        # Bot metrics
        if self.bot_manager:
            for bot_id, managed_bot in self.bot_manager.get_all_bots().items():
                state_value = 1 if managed_bot.state == "running" else 0
                metrics.append(f'multibot_bot_running{{bot_id="{bot_id}"}} {state_value}')

                if managed_bot.started_at:
                    from datetime import datetime

                    uptime = (datetime.utcnow() - managed_bot.started_at).total_seconds()
                    metrics.append(f'multibot_bot_uptime_seconds{{bot_id="{bot_id}"}} {uptime}')

            # Summary metrics
            total = len(self.bot_manager.get_all_bots())
            running = len(self.bot_manager.get_running_bots())
            metrics.append(f"multibot_bots_total {total}")
            metrics.append(f"multibot_bots_running {running}")

        # Database metrics
        if self.db and self.db._pool:
            metrics.append(f"multibot_db_pool_size {self.db.pool.get_size()}")
            metrics.append(f"multibot_db_pool_free {self.db.pool.get_idle_size()}")

        return web.Response(
            text="\n".join(metrics) + "\n",
            content_type="text/plain",
        )

    async def start(self) -> None:
        """Start the health check server."""
        self._runner = web.AppRunner(self.app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.host, self.port)
        await site.start()
        logger.info(f"Health server started on {self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the health check server."""
        if self._runner:
            await self._runner.cleanup()
            self._runner = None
            logger.info("Health server stopped")
