"""Health check implementations."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.core.bot_manager import BotManager
    from src.database.connection import DatabaseManager


async def check_database(db: DatabaseManager | None) -> dict[str, Any]:
    """Check database health."""
    if not db:
        return {"status": "unavailable", "message": "Database not configured"}

    try:
        is_healthy = await db.health_check()
        if is_healthy:
            return {
                "status": "healthy",
                "pool_size": db.pool.get_size(),
                "pool_free": db.pool.get_idle_size(),
            }
        else:
            return {"status": "unhealthy", "message": "Health check failed"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


async def check_bots(bot_manager: BotManager | None) -> dict[str, Any]:
    """Check bots health."""
    if not bot_manager:
        return {"status": "unavailable", "message": "Bot manager not configured"}

    bots = bot_manager.get_all_bots()
    running = len([b for b in bots.values() if b.state == "running"])
    total = len(bots)
    errors = len([b for b in bots.values() if b.state == "error"])

    status = "healthy" if running > 0 and errors == 0 else "degraded" if running > 0 else "unhealthy"

    return {
        "status": status,
        "total": total,
        "running": running,
        "stopped": len([b for b in bots.values() if b.state == "stopped"]),
        "errors": errors,
    }


async def get_health_status(
    bot_manager: BotManager | None = None,
    db: DatabaseManager | None = None,
) -> dict[str, Any]:
    """Get comprehensive health status."""
    components = {}

    # Check database
    if db:
        components["database"] = await check_database(db)

    # Check bots
    if bot_manager:
        components["bots"] = await check_bots(bot_manager)

    # Determine overall status
    statuses = [c.get("status", "unknown") for c in components.values()]
    if all(s == "healthy" for s in statuses):
        overall_status = "healthy"
    elif any(s == "unhealthy" for s in statuses):
        overall_status = "unhealthy"
    elif any(s == "degraded" for s in statuses):
        overall_status = "degraded"
    else:
        overall_status = "unknown"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "components": components,
    }
