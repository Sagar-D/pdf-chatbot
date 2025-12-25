import sqlite3
import config


def insert_user(username: str, password_hash: str) -> int:

    if not is_username_available(username):
        raise ValueError(f"The username '{username}' is already taken.")

    user_id = None
    with sqlite3.connect(config.RELATIONAL_DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO accounts (username, password_hash) values (?, ?) """,
            (username, password_hash),
        )
        cur.execute("SELECT user_id from accounts where username like ?", (username,))
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
    return user_id


def insert_user_chat_history(user_id: int, user_chat_history_path: str):

    if not user_id or not user_chat_history_path:
        raise ValueError(
            f"Required parameter 'user_id' or 'user_chat_history_path' is missing"
        )

    with sqlite3.connect(config.RELATIONAL_DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO user_chat_history (user_id, chat_json_path) values (?, ?) """,
            (user_id, user_chat_history_path),
        )
        conn.commit()
        cur.close()
    return user_chat_history_path


def is_username_available(username: str) -> bool:
    is_available = True
    with sqlite3.connect(config.RELATIONAL_DB_NAME) as conn:
        cur = conn.cursor()

        cur.execute("SELECT user_id from accounts where username like ?", (username,))
        results = cur.fetchall()
        if len(results) > 0:
            is_available = False
        conn.commit()
        cur.close()
    return is_available


def get_user(username: str) -> dict | None:
    user=None
    with sqlite3.connect(config.RELATIONAL_DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, user_name, password_hash from accounts where username like ?",
            (username,),
        )
        data = cur.fetchone()
        user = {"user_id": data[0], "username": data[1], "password_hash": data[2]}
        conn.commit()
        cur.close()
    return user


def get_user_chat_history(user_id) -> str | None:
    chat_history_json_path = None
    with sqlite3.connect(config.RELATIONAL_DB_NAME) as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT chat_json_path from user_chat_history where user_id = ?", (user_id,)
        )
        chat_history_json_path = cur.fetchone()[0]
        conn.commit()
        cur.close()
    return chat_history_json_path
