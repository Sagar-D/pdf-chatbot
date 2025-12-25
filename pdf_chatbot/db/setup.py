import sqlite3

import config


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

        default_users = [(1, "user", "password"), (2, "admin", "password")]
        default_chat_history = [
            (1, ".chat_history/user_1.json"),
            (2, ".chat_history/user_2.json"),
        ]
        cursor.executemany(
            """INSERT OR IGNORE INTO accounts (user_id, username, password_hash) VALUES (?, ?, ?)""",
            default_users,
        )
        cursor.executemany(
            """INSERT OR IGNORE INTO user_chat_history (user_id, chat_json_path) VALUES (?, ?)""",
            default_chat_history,
        )

        cursor.execute("""SELECT * FROM accounts""")

        rows = cursor.fetchall()
        for row in rows:
            print(
                f"user_id : {row[0]} | username : {row[1]} | password : {row[2]} | created_at : {row[3]} | "
            )

        conn.commit()
        cursor.close()


if __name__ == "__main__":
    initialize_db()
