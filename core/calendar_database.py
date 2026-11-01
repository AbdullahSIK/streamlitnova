
import os
import sqlite3
from pathlib import Path
from datetime import datetime


class CalendarDatabase:

    def __init__(self):

        app_data = os.environ.get("LOCALAPPDATA")

        if app_data:
            data_dir = Path(app_data) / "NOVA"
        else:
            data_dir = Path.home() / ".nova"

        data_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = data_dir / "calendar.db"
        self.initialize()

    def connect(self):

        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self):

        with self.connect() as connection:

            connection.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    event_date TEXT NOT NULL,
                    event_time TEXT DEFAULT '',
                    reminder_minutes INTEGER DEFAULT 0,
                    reminder_sent INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

    def add_event(
        self,
        title,
        description,
        event_date,
        event_time,
        reminder_minutes
    ):

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        with self.connect() as connection:

            cursor = connection.execute("""
                INSERT INTO events (
                    title,
                    description,
                    event_date,
                    event_time,
                    reminder_minutes,
                    reminder_sent,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, 0, ?)
            """, (
                title,
                description,
                event_date,
                event_time,
                reminder_minutes,
                now
            ))

            return cursor.lastrowid

    def update_event(
        self,
        event_id,
        title,
        description,
        event_date,
        event_time,
        reminder_minutes
    ):

        with self.connect() as connection:

            connection.execute("""
                UPDATE events
                SET title = ?,
                    description = ?,
                    event_date = ?,
                    event_time = ?,
                    reminder_minutes = ?,
                    reminder_sent = 0
                WHERE id = ?
            """, (
                title,
                description,
                event_date,
                event_time,
                reminder_minutes,
                event_id
            ))

    def delete_event(self, event_id):

        with self.connect() as connection:

            connection.execute(
                "DELETE FROM events WHERE id = ?",
                (event_id,)
            )

    def get_event(self, event_id):

        with self.connect() as connection:

            row = connection.execute(
                "SELECT * FROM events WHERE id = ?",
                (event_id,)
            ).fetchone()

        return dict(row) if row else None

    def get_events(self, event_date=None):

        with self.connect() as connection:

            if event_date:

                rows = connection.execute("""
                    SELECT * FROM events
                    WHERE event_date = ?
                    ORDER BY event_time ASC, id ASC
                """, (event_date,)).fetchall()

            else:

                rows = connection.execute("""
                    SELECT * FROM events
                    ORDER BY event_date ASC,
                             event_time ASC,
                             id ASC
                """).fetchall()

        return [dict(row) for row in rows]

    def get_upcoming_events(self, limit=10):

        today = datetime.now().date().isoformat()

        with self.connect() as connection:

            rows = connection.execute("""
                SELECT * FROM events
                WHERE event_date >= ?
                ORDER BY event_date ASC,
                         event_time ASC,
                         id ASC
                LIMIT ?
            """, (today, limit)).fetchall()

        return [dict(row) for row in rows]

    def get_pending_reminders(self):

        now = datetime.now()

        with self.connect() as connection:

            rows = connection.execute("""
                SELECT * FROM events
                WHERE reminder_minutes > 0
                  AND reminder_sent = 0
            """).fetchall()

            due_events = []
            expired_ids = []

            for row in rows:

                event = dict(row)

                try:

                    event_datetime = datetime.strptime(
                        f"{event['event_date']} {event['event_time']}",
                        "%Y-%m-%d %H:%M"
                    )

                except (ValueError, TypeError):
                    continue

                reminder_time = (
                    event_datetime.timestamp()
                    - event["reminder_minutes"] * 60
                )

                # Reminder is due, but the event hasn't started.
                if (
                    now.timestamp() >= reminder_time
                    and now < event_datetime
                ):
                    due_events.append(event)

                # Don't show old reminders after restarting NOVA.
                elif now >= event_datetime:
                    expired_ids.append(event["id"])

            # Mark expired reminders so they aren't checked again.
            if expired_ids:

                connection.executemany("""
                    UPDATE events
                    SET reminder_sent = 1
                    WHERE id = ?
                """, [(event_id,) for event_id in expired_ids])

        return due_events

    def mark_reminder_sent(self, event_id):

        with self.connect() as connection:

            connection.execute("""
                UPDATE events
                SET reminder_sent = 1
                WHERE id = ?
            """, (event_id,))
