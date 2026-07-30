import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler

import db
import scheduler
from parser import parse_news_command, ParseError
from validator import ValidationError
from fetchers.errors import FetchError
from fetchers import crypto, stocks_us, stocks_in
from formatter import format_news

logger = logging.getLogger(__name__)


async def crypto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        parsed = parse_news_command(update.message.text, "crypto")

        if parsed.has_time:
            schedule_id = scheduler.create_schedule(
                update.effective_chat.id, parsed, context.application
            )
            await update.message.reply_text(
                f"✅ Scheduled! ID: #{schedule_id} — "
                f"Crypto news (top {parsed.count}) daily at {parsed.time_str} UTC"
            )
        else:
            items = await crypto.fetch(parsed.count)
            msg = format_news(items, "crypto")
            await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

    except ParseError as exc:
        await update.message.reply_text(
            f"{exc}\n\nUsage: /crypto top <N> [time HH:MMam/pm]"
        )
    except ValidationError as exc:
        await update.message.reply_text(str(exc))
    except FetchError as exc:
        logger.warning("Fetch failed in crypto_handler: %s", exc)
        await update.message.reply_text(
            "News service temporarily unavailable. Please try again later."
        )
    except Exception:
        logger.error("Unexpected error in crypto_handler", exc_info=True)
        await update.message.reply_text(
            "An unexpected error occurred. The issue has been logged."
        )


async def stocks_us_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        parsed = parse_news_command(update.message.text, "stocks_us")

        if parsed.has_time:
            schedule_id = scheduler.create_schedule(
                update.effective_chat.id, parsed, context.application
            )
            await update.message.reply_text(
                f"✅ Scheduled! ID: #{schedule_id} — "
                f"US stock news (top {parsed.count}) daily at {parsed.time_str} UTC"
            )
        else:
            items = await stocks_us.fetch(parsed.count)
            msg = format_news(items, "stocks_us")
            await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

    except ParseError as exc:
        await update.message.reply_text(
            f"{exc}\n\nUsage: /stocks_us top <N> [time HH:MMam/pm]"
        )
    except ValidationError as exc:
        await update.message.reply_text(str(exc))
    except FetchError as exc:
        logger.warning("Fetch failed in stocks_us_handler: %s", exc)
        await update.message.reply_text(
            "News service temporarily unavailable. Please try again later."
        )
    except Exception:
        logger.error("Unexpected error in stocks_us_handler", exc_info=True)
        await update.message.reply_text(
            "An unexpected error occurred. The issue has been logged."
        )


async def stocks_in_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        parsed = parse_news_command(update.message.text, "stocks_in")

        if parsed.has_time:
            schedule_id = scheduler.create_schedule(
                update.effective_chat.id, parsed, context.application
            )
            await update.message.reply_text(
                f"✅ Scheduled! ID: #{schedule_id} — "
                f"Indian stock news (top {parsed.count}) daily at {parsed.time_str} UTC"
            )
        else:
            items = await stocks_in.fetch(parsed.count)
            msg = format_news(items, "stocks_in")
            await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

    except ParseError as exc:
        await update.message.reply_text(
            f"{exc}\n\nUsage: /stocks_in top <N> [time HH:MMam/pm]"
        )
    except ValidationError as exc:
        await update.message.reply_text(str(exc))
    except FetchError as exc:
        logger.warning("Fetch failed in stocks_in_handler: %s", exc)
        await update.message.reply_text(
            "News service temporarily unavailable. Please try again later."
        )
    except Exception:
        logger.error("Unexpected error in stocks_in_handler", exc_info=True)
        await update.message.reply_text(
            "An unexpected error occurred. The issue has been logged."
        )


async def list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        schedules = db.get_schedules_for_user(update.effective_chat.id)

        if not schedules:
            await update.message.reply_text("You have no active schedules.")
            return

        lines = [
            f"#{s.id} | {s.topic} | top {s.count} | {s.delivery_time} UTC"
            for s in schedules
        ]
        await update.message.reply_text(
            "Your active schedules:\n\n" + "\n".join(lines)
        )

    except Exception:
        logger.error("Unexpected error in list_handler", exc_info=True)
        await update.message.reply_text(
            "An unexpected error occurred. The issue has been logged."
        )


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if not context.args:
            await update.message.reply_text("Usage: /cancel <schedule_id>")
            return

        arg = context.args[0]
        try:
            schedule_id = int(arg)
        except ValueError:
            await update.message.reply_text(
                "Invalid schedule ID. Usage: /cancel <schedule_id>"
            )
            return

        removed = scheduler.cancel_schedule(
            schedule_id, update.effective_chat.id, context.application
        )

        if removed:
            await update.message.reply_text(f"✅ Schedule #{schedule_id} cancelled.")
        else:
            await update.message.reply_text(
                f"❌ Schedule #{schedule_id} not found or doesn't belong to you."
            )

    except Exception:
        logger.error("Unexpected error in cancel_handler", exc_info=True)
        await update.message.reply_text(
            "An unexpected error occurred. The issue has been logged."
        )


_HELP_TEXT = """<b>📰 News Bot Commands</b>

<b>/crypto top &lt;N&gt;</b>
  Fetch the top N crypto news items instantly.
  Example: <code>/crypto top 5</code>

<b>/crypto top &lt;N&gt; time &lt;HH:MMam/pm&gt;</b>
  Schedule daily crypto news delivery.
  Example: <code>/crypto top 5 time 10:00pm</code>

<b>/stocks_us top &lt;N&gt;</b>
  Fetch the top N US stock market news items instantly.
  Example: <code>/stocks_us top 10</code>

<b>/stocks_us top &lt;N&gt; time &lt;HH:MMam/pm&gt;</b>
  Schedule daily US stock news delivery.
  Example: <code>/stocks_us top 10 time 9:30am</code>

<b>/stocks_in top &lt;N&gt;</b>
  Fetch the top N Indian stock market news items instantly.
  Example: <code>/stocks_in top 3</code>

<b>/stocks_in top &lt;N&gt; time &lt;HH:MMam/pm&gt;</b>
  Schedule daily Indian stock news delivery.
  Example: <code>/stocks_in top 3 time 8:00am</code>

<b>/list</b>
  Show all your active schedules with their IDs.
  Example: <code>/list</code>

<b>/cancel &lt;schedule_id&gt;</b>
  Cancel a scheduled delivery by its ID.
  Example: <code>/cancel 3</code>

<b>/help</b>
  Show this help message.

<i>N must be between 1 and 20. Times are in UTC.</i>"""


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(_HELP_TEXT, parse_mode=ParseMode.HTML)


def register_handlers(app) -> None:
    app.add_handler(CommandHandler("crypto", crypto_handler))
    app.add_handler(CommandHandler("stocks_us", stocks_us_handler))
    app.add_handler(CommandHandler("stocks_in", stocks_in_handler))
    app.add_handler(CommandHandler("list", list_handler))
    app.add_handler(CommandHandler("cancel", cancel_handler))
    app.add_handler(CommandHandler("help", help_handler))
