import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")
DB_PATH = os.environ.get("DB_PATH", "data/schedules.db")
LOG_FILE = os.environ.get("LOG_FILE", "logs/bot.log")

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def _setup_logging():
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    if root.handlers:
        return  # already set up

    root.setLevel(logging.INFO)
    fmt = logging.Formatter(_LOG_FORMAT)

    fh = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    root.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root.addHandler(sh)


_setup_logging()
