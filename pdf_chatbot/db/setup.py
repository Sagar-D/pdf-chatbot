import sqlite3
from pdf_chatbot import config
from pathlib import Path
from pdf_chatbot.user.account import hash_password
import json

default_users = [(1, "user", hash_password("password")), (2, "admin", hash_password("password"))]
default_chat_history = [
    (1, ".chat_history/user_1.json"),
    (2, ".chat_history/user_2.json"),
]

def setup_chat_history() :

    for chat_history_obj in default_chat_history :
        user_chat_history_path = chat_history_obj[1]
        file_path = Path(user_chat_history_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as chat_file:
            json.dump([], chat_file)

def initialize_db():

    with sqlite3.connect(config.RELATIONAL_DB_NAME) as conn:
        conn: sqlite3.Connection

        cursor = conn.cursor()

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS accounts(
            user_id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS user_chat_history(
            user_id INTEGER PRIMARY KEY,
            chat_json_path TEXT UNIQUE NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES accounts (user_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
            """
        )

        cursor.executemany(
            """INSERT OR IGNORE INTO accounts (user_id, username, password_hash) VALUES (?, ?, ?)""",
            default_users,
        )
        cursor.executemany(
            """INSERT OR IGNORE INTO user_chat_history (user_id, chat_json_path) VALUES (?, ?)""",
            default_chat_history,
        )
        conn.commit()
        cursor.close()


if __name__ == "__main__":
    setup_chat_history()
    initialize_db()
