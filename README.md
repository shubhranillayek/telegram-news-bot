# Telegram News Bot — Python Crypto and Stock News Automation

Telegram News Bot is a Python project by [Shubhranil Layek](https://github.com/shubhranillayek) for fetching crypto, US stock and Indian stock news through commands or daily schedules. Schedules are stored in SQLite, and stock news has a Yahoo Finance RSS fallback. External news availability depends on the upstream providers.

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
git clone https://github.com/shubhranillayek/telegram-news-bot.git
cd telegram-news-bot
pip install -r requirements.txt
```

**2. Get API keys**

- `TELEGRAM_BOT_TOKEN` — message [@BotFather](https://t.me/BotFather) on Telegram, create a bot with `/newbot`
- `NEWSAPI_KEY` — obtain a key from [newsapi.org](https://newsapi.org); check its current plan limits and permitted uses.

**3. Configure**

Create `.env` in the repository root and replace these placeholders with your own keys:

```dotenv
TELEGRAM_BOT_TOKEN=replace_with_your_telegram_bot_token
NEWSAPI_KEY=replace_with_your_newsapi_key
```

Keep `.env` private. Never commit real tokens or API keys to GitHub.

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
| Crypto | CoinGecko (configured public endpoint) | — |
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

## Frequently asked questions

### Which timezone do schedules use?

All command times are UTC. For example, `/crypto top 5 time 10:00pm` requests a daily schedule at 22:00 UTC.

### Do schedules survive a restart?

Schedules are stored in SQLite and restored when the bot starts. Keep the database file persistent when deploying, and keep the bot process running for scheduled delivery.

### What is required to run it?

Python 3.11+, the packages in `requirements.txt`, a Telegram bot token and a NewsAPI key. Provider availability, quotas and API compatibility must be checked for your deployment; this repository is not a hosted news service.

## License

MIT
