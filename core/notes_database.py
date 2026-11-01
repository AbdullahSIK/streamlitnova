
import os
import sqlite3
from pathlib import Path


class NotesDatabase:

    def __init__(self):
        app_data = os.environ.get("LOCALAPPDATA")

        if app_data:
            data_dir = Path(app_data) / "NOVA"
        else:
            data_dir = Path.home() / ".nova"

        data_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = data_dir / "notes.db"
        self.initialize()

    def connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self):

        with self.connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT DEFAULT '',
                    pinned INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

    def get_notes(self, search=""):

        with self.connect() as connection:

            if search.strip():
                pattern = f"%{search.strip()}%"

                rows = connection.execute("""
                    SELECT * FROM notes
                    WHERE title LIKE ? OR content LIKE ?
                    ORDER BY pinned DESC, updated_at DESC
                """, (pattern, pattern)).fetchall()

            else:
                rows = connection.execute("""
                    SELECT * FROM notes
                    ORDER BY pinned DESC, updated_at DESC
                """).fetchall()

        return [dict(row) for row in rows]

    def get_note(self, note_id):

        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM notes WHERE id = ?",
                (note_id,)
            ).fetchone()

        return dict(row) if row else None

    def add_note(self, title, content, pinned=0):

        from datetime import datetime

        now = datetime.now().isoformat(timespec="seconds")

        with self.connect() as connection:

            cursor = connection.execute("""
                INSERT INTO notes
                (title, content, pinned, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                title,
                content,
                int(pinned),
                now,
                now
            ))

            return cursor.lastrowid

    def update_note(self, note_id, title, content, pinned):

        from datetime import datetime

        now = datetime.now().isoformat(timespec="seconds")

        with self.connect() as connection:
            connection.execute("""
                UPDATE notes
                SET title = ?,
                    content = ?,
                    pinned = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                title,
                content,
                int(pinned),
                now,
                note_id
            ))

    def delete_note(self, note_id):

        with self.connect() as connection:
            connection.execute(
                "DELETE FROM notes WHERE id = ?",
                (note_id,)
            )
    