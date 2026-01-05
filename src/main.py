"""Entry point for the Telegram Multibot System."""

from __future__ import annotations

import asyncio
import sys

from dotenv import load_dotenv


def main() -> int:
    """Main entry point."""
    # Load environment variables from .env file
    load_dotenv()

    # Import after loading env to ensure env vars are available
    from src.core.app import MultibotApplication
    from src.core.config import AppConfig
    from src.utils.logging import setup_logging

    # Load configuration
    config = AppConfig()

    # Setup logging
    setup_logging(
        level=config.log_level,
        format=config.log_format,
    )

    # Create and run application
    app = MultibotApplication(config)

    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        pass  # Handled by signal handler

    return 0


if __name__ == "__main__":
    sys.exit(main())
