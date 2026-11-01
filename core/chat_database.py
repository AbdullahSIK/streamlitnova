
import sqlite3
from pathlib import Path
from datetime import datetime


class ChatDatabase:

    def __init__(self):
        app_data = Path.home() / ".nova"
        app_data.mkdir(parents=True, exist_ok=True)

        self.db_path = app_data / "chats.db"

        self.create_tables()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def create_tables(self):
        with self.connect() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    sender TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id)
                        REFERENCES conversations(id)
                        ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_messages_conversation
                ON messages(conversation_id)
            """)

            cursor.execute("PRAGMA foreign_keys = ON")

            connection.commit()

    def create_conversation(self, title="New Chat"):
        now = datetime.now().isoformat(timespec="seconds")

        with self.connect() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO conversations (
                    title, created_at, updated_at
                )
                VALUES (?, ?, ?)
            """, (title, now, now))

            return cursor.lastrowid

    def save_message(self, conversation_id, sender, content):
        now = datetime.now().isoformat(timespec="seconds")

        with self.connect() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO messages (
                    conversation_id,
                    sender,
                    content,
                    created_at
                )
                VALUES (?, ?, ?, ?)
            """, (conversation_id, sender, content, now))

            connection.execute("""
                UPDATE conversations
                SET updated_at = ?
                WHERE id = ?
            """, (now, conversation_id))

    def update_title(self, conversation_id, title):
        with self.connect() as connection:
            connection.execute("""
                UPDATE conversations
                SET title = ?
                WHERE id = ?
            """, (title, conversation_id))

    def get_conversations(self):
        with self.connect() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT id, title, created_at, updated_at
                FROM conversations
                ORDER BY updated_at DESC
            """)

            return cursor.fetchall()

    def get_messages(self, conversation_id):
        with self.connect() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT sender, content
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id ASC
            """, (conversation_id,))

            return cursor.fetchall()

    def delete_conversation(self, conversation_id):
        with self.connect() as connection:
            connection.execute("PRAGMA foreign_keys = ON")

            connection.execute("""
                DELETE FROM messages
                WHERE conversation_id = ?
            """, (conversation_id,))

            connection.execute("""
                DELETE FROM conversations
                WHERE id = ?
            """, (conversation_id,))

    def delete_all_conversations(self):
        with self.connect() as connection:
            connection.execute("PRAGMA foreign_keys = ON")

            connection.execute("DELETE FROM messages")
            connection.execute("DELETE FROM conversations")
