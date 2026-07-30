import asyncio

import config
import db
import scheduler
from handlers import register_handlers
from telegram.ext import Application


async def post_init(app) -> None:
    # The event loop is running here — safe to capture it for the background scheduler
    scheduler.set_loop(asyncio.get_event_loop())
    scheduler.restore_schedules(app)


def main():
    if not config.BOT_TOKEN:
        print("Set TELEGRAM_BOT_TOKEN in your .env file first.")
        raise SystemExit(1)

    db.init()
    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    register_handlers(app)
    scheduler.start()   # starts APScheduler only — no loop capture here
    app.run_polling()


if __name__ == "__main__":
    main()
