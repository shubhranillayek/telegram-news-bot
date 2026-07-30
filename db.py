import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from config import DB_PATH


@dataclass
class ScheduleRow:
    id: int
    chat_id: int
    topic: str
    count: int
    delivery_time: str  # "HH:MM" 24-hour UTC
    created_at: str     # ISO-8601 UTC


_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schedules (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id       INTEGER NOT NULL,
    topic         TEXT    NOT NULL,
    count         INTEGER NOT NULL,
    delivery_time TEXT    NOT NULL,
    created_at    TEXT    NOT NULL
);
"""


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_schedule(row: sqlite3.Row) -> ScheduleRow:
    return ScheduleRow(
        id=row["id"],
        chat_id=row["chat_id"],
        topic=row["topic"],
        count=row["count"],
        delivery_time=row["delivery_time"],
        created_at=row["created_at"],
    )


def init() -> None:
    # create db file and parent dirs if they don't exist
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with _get_connection() as conn:
        conn.execute(_CREATE_TABLE_SQL)
        conn.commit()


def insert_schedule(
    chat_id: int,
    topic: str,
    count: int,
    delivery_time: str,
) -> int:
    # returns the new row's auto-increment id
    created_at = datetime.now(timezone.utc).isoformat()
    with _get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO schedules (chat_id, topic, count, delivery_time, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (chat_id, topic, count, delivery_time, created_at),
        )
        conn.commit()
        return cursor.lastrowid


def delete_schedule(schedule_id: int, chat_id: int) -> bool:
    # only delete if the schedule belongs to this user
    with _get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM schedules WHERE id = ? AND chat_id = ?",
            (schedule_id, chat_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_schedules_for_user(chat_id: int) -> list[ScheduleRow]:
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM schedules WHERE chat_id = ? ORDER BY id",
            (chat_id,),
        ).fetchall()
    return [_row_to_schedule(r) for r in rows]


def get_all_schedules() -> list[ScheduleRow]:
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM schedules ORDER BY id"
        ).fetchall()
    return [_row_to_schedule(r) for r in rows]
