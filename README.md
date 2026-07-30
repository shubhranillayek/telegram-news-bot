# telegram-news-bot

A Telegram bot that fetches crypto, US stock, and Indian stock market news. Send a command and get the latest headlines instantly, or schedule it to run daily at a time you pick.

## What it does

- Instant news delivery — send `/crypto top 5` and get 5 headlines right now
- Daily scheduling — pick a time, get news every day automatically
- Multiple schedules per user, each with its own ID
- Schedules survive bot restarts (stored in SQLite)
- Falls back to Yahoo Finance RSS if NewsAPI is down
- Each user only sees their own schedules

## Setup

**1. Clone and install**
```bash
git clone https://github.com/YOUR_USERNAME/telegram-news-bot.git
cd telegram-news-bot
pip install -r requirements.txt
```

**2. Get API keys**

- `TELEGRAM_BOT_TOKEN` — message [@BotFather](https://t.me/BotFather) on Telegram, create a bot with `/newbot`
- `NEWSAPI_KEY` — free signup at [newsapi.org](https://newsapi.org) (100 requests/day on the free tier)

**3. Configure**
```bash
cp .env.example .env
# fill in your two keys
```

**4. Run**
```bash
python bot.py
```

## Commands

```
/crypto top 5                   get top 5 crypto headlines now
/stocks_us top 10               get top 10 US stock headlines now
/stocks_in top 3                get top 3 Indian stock headlines now

/crypto top 5 time 10:00pm      schedule daily crypto news at 10 PM UTC
/stocks_us top 10 time 9:30am   schedule daily US stock news at 9:30 AM UTC
/stocks_in top 3 time 8:00am    schedule daily Indian stock news at 8 AM UTC

/list                           show your active schedules
/cancel 3                       cancel schedule #3
/help                           show all commands
```

N must be between 1 and 20. All times are UTC.

## Data sources

| Topic | Primary | Fallback |
|---|---|---|
| Crypto | CoinGecko (no key needed) | — |
| US Stocks | NewsAPI | Yahoo Finance RSS |
| Indian Stocks | NewsAPI | Yahoo Finance BSE RSS |

## Configuration

All config is via environment variables (or a `.env` file):

| Variable | Default | Notes |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | required |
| `NEWSAPI_KEY` | — | required |
| `DB_PATH` | `data/schedules.db` | auto-created |
| `LOG_FILE` | `logs/bot.log` | 5 MB rotating, 3 backups |

## Project layout

```
telegram-news-bot/
├── bot.py           # entry point
├── config.py        # env vars + logging
├── handlers.py      # command handlers
├── parser.py        # parses command strings into structured objects
├── validator.py     # validates count and time inputs
├── formatter.py     # builds HTML messages from news items
├── scheduler.py     # APScheduler wrapper for daily jobs
├── db.py            # SQLite layer
├── fetchers/
│   ├── errors.py    # FetchError
│   ├── crypto.py    # CoinGecko
│   ├── stocks_us.py # NewsAPI + Yahoo Finance RSS (US)
│   └── stocks_in.py # NewsAPI + Yahoo Finance RSS (India)
├── data/            # SQLite DB lives here (auto-created)
└── logs/            # log file lives here (auto-created)
```

## Requirements

Python 3.11+. See `requirements.txt` for package versions.

## License

MIT
