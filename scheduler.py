import asyncio
import logging
from datetime import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger  # noqa: F401 — available for callers

import db
from fetchers.errors import FetchError
from formatter import format_news
from parser import ParsedCommand

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler()
_loop: asyncio.AbstractEventLoop | None = None


def start() -> None:
    _scheduler.start()
    logger.info("Background scheduler started.")


def set_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _loop
    _loop = loop
    logger.info("Event loop captured for scheduled deliveries.")


def create_schedule(chat_id: int, parsed: ParsedCommand, app) -> int:
    schedule_id = db.insert_schedule(
        chat_id,
        parsed.topic,
        parsed.count,
        parsed.delivery_time.strftime("%H:%M"),
    )
    _add_job(schedule_id, chat_id, parsed.topic, parsed.count,
             parsed.delivery_time, app)
    logger.info(
        "Created schedule #%d for chat %d: %s top %d at %s",
        schedule_id, chat_id, parsed.topic, parsed.count,
        parsed.delivery_time.strftime("%H:%M"),
    )
    return schedule_id


def cancel_schedule(schedule_id: int, chat_id: int, app) -> bool:
    removed = db.delete_schedule(schedule_id, chat_id)
    if removed:
        try:
            _scheduler.remove_job(str(schedule_id))
            logger.info("Removed APScheduler job for schedule #%d", schedule_id)
        except Exception:
            logger.warning(
                "Could not remove APScheduler job for schedule #%d (not found in scheduler)",
                schedule_id,
            )
    return removed


def restore_schedules(app) -> None:
    rows = db.get_all_schedules()
    for row in rows:
        h, m = map(int, row.delivery_time.split(":"))
        t = time(h, m)
        _add_job(row.id, row.chat_id, row.topic, row.count, t, app)
        logger.info(
            "Restored schedule #%d for chat %d (%s top %d at %02d:%02d)",
            row.id, row.chat_id, row.topic, row.count, h, m,
        )
    logger.info("Restored %d schedule(s) from database.", len(rows))


def _add_job(
    schedule_id: int,
    chat_id: int,
    topic: str,
    count: int,
    delivery_time: time,
    app,
) -> None:
    _scheduler.add_job(
        func=_deliver,
        trigger="cron",
        hour=delivery_time.hour,
        minute=delivery_time.minute,
        id=str(schedule_id),
        kwargs={
            "schedule_id": schedule_id,
            "chat_id": chat_id,
            "topic": topic,
            "count": count,
            "app": app,
        },
        replace_existing=True,
    )


def _deliver(
    schedule_id: int,
    chat_id: int,
    topic: str,
    count: int,
    app,
) -> None:
    # APScheduler runs this in a background thread, so we use run_coroutine_threadsafe
    # to safely dispatch async work onto the bot's event loop
    if _loop is None:
        logger.error("Scheduler loop not set up — call scheduler.start() first")
        return
    logger.info(
        "Delivering schedule #%d to chat %d: %s top %d",
        schedule_id, chat_id, topic, count,
    )
    try:
        items = asyncio.run_coroutine_threadsafe(
            _fetch(topic, count), _loop
        ).result()

        msg = format_news(items, topic, schedule_id=schedule_id)

        asyncio.run_coroutine_threadsafe(
            app.bot.send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode="HTML",
            ),
            _loop,
        ).result()

        logger.info(
            "Successfully delivered schedule #%d to chat %d", schedule_id, chat_id
        )

    except FetchError as exc:
        logger.error(
            "FetchError delivering schedule #%d to chat %d: %s",
            schedule_id, chat_id, exc,
        )
        _send_error(
            app,
            chat_id,
            "News service temporarily unavailable. Please try again later.",
        )

    except Exception:
        logger.error(
            "Unexpected error delivering schedule #%d to chat %d",
            schedule_id, chat_id,
            exc_info=True,
        )
        _send_error(
            app,
            chat_id,
            "An unexpected error occurred. The issue has been logged.",
        )


async def _fetch(topic: str, count: int):
    if topic == "crypto":
        from fetchers import crypto
        return await crypto.fetch(count)
    elif topic == "stocks_us":
        from fetchers import stocks_us
        return await stocks_us.fetch(count)
    elif topic == "stocks_in":
        from fetchers import stocks_in
        return await stocks_in.fetch(count)
    else:
        raise ValueError(f"Unknown topic: {topic!r}")


def _send_error(app, chat_id: int, message: str) -> None:
    if _loop is None:
        logger.error("Scheduler loop not set up — call scheduler.start() first")
        return
    try:
        asyncio.run_coroutine_threadsafe(
            app.bot.send_message(chat_id=chat_id, text=message),
            _loop,
        ).result()
    except Exception:
        logger.error(
            "Failed to send error message to chat %d", chat_id, exc_info=True
        )
