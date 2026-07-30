import datetime
import re


class ValidationError(ValueError):
    """Raised when user-supplied input fails validation."""


def validate_count(n: int) -> None:
    if not (1 <= n <= 20):
        raise ValidationError(f"Count must be between 1 and 20, got {n}.")


# matches "HH:MMam/pm" or "HH:MM am/pm", case-insensitive, optional space
_TIME_RE = re.compile(
    r"^(\d{1,2}):(\d{2})\s*(am|pm)$",
    re.IGNORECASE,
)


def validate_time_format(time_str: str) -> datetime.time:
    # parse a 12-hour time string like "10:00pm" or "9:30 AM" into datetime.time
    _invalid_msg = (
        f"Invalid time format '{time_str}'. "
        "Expected HH:MMam/pm (e.g. 10:00pm, 9:30am)."
    )

    match = _TIME_RE.match(time_str.strip())
    if not match:
        raise ValidationError(_invalid_msg)

    hours_str, minutes_str, meridiem = match.groups()
    hours = int(hours_str)
    minutes = int(minutes_str)

    if not (1 <= hours <= 12) or not (0 <= minutes <= 59):
        raise ValidationError(_invalid_msg)

    meridiem_lower = meridiem.lower()
    if meridiem_lower == "am":
        # 12:XXam → 0:XX (midnight hour)
        hour_24 = 0 if hours == 12 else hours
    else:
        # 12:XXpm → 12:XX (noon); others add 12
        hour_24 = 12 if hours == 12 else hours + 12

    return datetime.time(hour_24, minutes)
