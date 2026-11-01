
import sqlite3
import os
from pathlib import Path


class Database:

    def __init__(self):

        app_data = os.getenv("LOCALAPPDATA")

        if app_data:
            data_folder = Path(app_data) / "NOVA"
        else:
            data_folder = Path.home() / ".nova"

        data_folder.mkdir(parents=True, exist_ok=True)

        self.db_path = data_folder / "nova.db"

        self.initialize()

    def connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self):

        with self.connect() as connection:

            connection.execute("""
                CREATE TABLE IF NOT EXISTS tasks (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    title TEXT NOT NULL,

                    description TEXT DEFAULT '',

                    priority TEXT DEFAULT 'Medium',

                    due_date TEXT NOT NULL,

                    completed INTEGER DEFAULT 0,

                    created_at TEXT DEFAULT CURRENT_TIMESTAMP

                )
            """)

    def get_tasks(self):

        with self.connect() as connection:

            rows = connection.execute("""
                SELECT * FROM tasks

                ORDER BY
                    completed ASC,

                    CASE priority
                        WHEN 'High' THEN 1
                        WHEN 'Medium' THEN 2
                        WHEN 'Low' THEN 3
                    END,

                    due_date ASC,
                    id DESC
            """).fetchall()

            return [dict(row) for row in rows]

    def add_task(self, title, description, priority, due_date):

        with self.connect() as connection:

            connection.execute("""
                INSERT INTO tasks
                (title, description, priority, due_date)

                VALUES (?, ?, ?, ?)
            """, (title, description, priority, due_date))

    def update_task(self, task_id, title, description,
                    priority, due_date):

        with self.connect() as connection:

            connection.execute("""
                UPDATE tasks

                SET title = ?,
                    description = ?,
                    priority = ?,
                    due_date = ?

                WHERE id = ?
            """, (
                title,
                description,
                priority,
                due_date,
                task_id
            ))

    def set_completed(self, task_id, completed):

        with self.connect() as connection:

            connection.execute("""
                UPDATE tasks
                SET completed = ?
                WHERE id = ?
            """, (int(completed), task_id))

    def delete_task(self, task_id):

        with self.connect() as connection:

            connection.execute("""
                DELETE FROM tasks
                WHERE id = ?
            """, (task_id,))
