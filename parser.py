import datetime
import re
from dataclasses import dataclass

from validator import validate_count, validate_time_format

VALID_TOPICS = ("crypto", "stocks_us", "stocks_in")


class ParseError(ValueError):
    """Raised when a command string doesn't match any recognised structure."""


@dataclass
class ParsedCommand:
    # structured result of a parsed news command
    topic: str
    count: int
    has_time: bool
    delivery_time: datetime.time | None
    time_str: str | None


# matches the command head, with optional @botname suffix
#   e.g. /crypto, /stocks_us@MyBot
_CMD_HEAD_RE = re.compile(
    r"^/(?P<cmd>\w+)(?:@\w+)?",
    re.IGNORECASE,
)

# matches "top N" with an optional "time HH:MMam/pm" after it
_BODY_RE = re.compile(
    r"""
    \s+ top \s+ (?P<count>\d+)          # required:  "top N"
    (?:                                  # optional:  "time HH:MMam/pm"
        \s+ time \s+ (?P<time_str>\S+)
    )?
    \s*$                                 # no trailing garbage
    """,
    re.VERBOSE | re.IGNORECASE,
)


def parse_news_command(text: str, topic: str) -> ParsedCommand:
    # parses raw command text like "/crypto top 5 time 10:00pm" into a ParsedCommand
    if topic not in VALID_TOPICS:
        raise ParseError(
            f"Unknown topic '{topic}'. "
            f"Must be one of: {', '.join(VALID_TOPICS)}."
        )

    text = text.strip()

    head_match = _CMD_HEAD_RE.match(text)
    if not head_match:
        raise ParseError(
            f"Could not parse command. "
            f"Expected: /{topic} top <N> [time HH:MMam/pm]"
        )

    remainder = text[head_match.end():]

    body_match = _BODY_RE.match(remainder)
    if not body_match:
        raise ParseError(
            f"Could not parse command. "
            f"Expected: /{topic} top <N> [time HH:MMam/pm]"
        )

    raw_count = int(body_match.group("count"))
    raw_time_str = body_match.group("time_str")

    validate_count(raw_count)

    delivery_time: datetime.time | None = None
    has_time = raw_time_str is not None

    if has_time:
        delivery_time = validate_time_format(raw_time_str)

    return ParsedCommand(
        topic=topic,
        count=raw_count,
        has_time=has_time,
        delivery_time=delivery_time,
        time_str=raw_time_str if has_time else None,
    )
