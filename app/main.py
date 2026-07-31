from __future__ import annotations

import logging

from app.bot.application import build_application
from app.settings import settings


def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    app = build_application(settings)
    logging.getLogger(__name__).info("Lenswire bot starting")
    app.run_polling()


if __name__ == "__main__":
    main()
