from dataclasses import dataclass
from datetime import datetime


@dataclass
class NewsItem:
    headline: str
    url: str | None
    source: str


_TOPIC_LABELS: dict[str, str] = {
    "crypto": "Crypto News",
    "stocks_us": "US Stock News",
    "stocks_in": "Indian Stock News",
}


def _build_header(topic: str, schedule_id: int | None, ts: datetime) -> str:
    label = _TOPIC_LABELS[topic]
    ts_str = ts.strftime("%Y-%m-%d %H:%M UTC")
    if schedule_id is not None:
        return f"<b>{label}</b> | Schedule #{schedule_id} | {ts_str}"
    return f"<b>{label}</b> | {ts_str}"


def format_news(
    items: list[NewsItem],
    topic: str,
    schedule_id: int | None = None,
    now: datetime | None = None,
) -> str:
    header = _build_header(topic, schedule_id, now or datetime.utcnow())
    lines: list[str] = [header]

    for i, item in enumerate(items, start=1):
        if item.url is not None:
            lines.append(f'{i}. <a href="{item.url}">{item.headline}</a>')
        else:
            lines.append(f"{i}. {item.headline}")

    return "\n".join(lines)
