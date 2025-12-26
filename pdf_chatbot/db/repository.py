import sqlite3
from pdf_chatbot import config


def insert_user(username: str, password_hash: str) -> int:

    if not is_username_available(username):
        raise ValueError(f"The username '{username}' is already taken.")

    user_id = None
    with sqlite3.connect(config.RELATIONAL_DB_NAME) as conn:
        cur = conn.cursor()
        user_id = cur.execute(
            """INSERT INTO accounts (username, password_hash) values (?, ?) RETURNING user_id""",
            (username, password_hash),
        )
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

        cur.execute(
            "SELECT user_id FROM accounts WHERE username = ? LIMIT 1", (username,)
        )
        if cur.fetchone():
            is_available = False
        cur.close()
    return is_available


def get_user(username: str) -> dict | None:
    user = None
    with sqlite3.connect(config.RELATIONAL_DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, username, password_hash FROM accounts WHERE username = ? LIMIT 1",
            (username,),
        )
        data = cur.fetchone()
        if data:
            user = {"user_id": data[0], "username": data[1], "password_hash": data[2]}
        cur.close()
    return user


def get_user_chat_history(user_id) -> str | None:
    chat_history_json_path = None
    with sqlite3.connect(config.RELATIONAL_DB_NAME) as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT chat_json_path FROM user_chat_history WHERE user_id = ? LIMIT 1",
            (user_id,),
        )
        result = cur.fetchone()
        if result:
            chat_history_json_path = result[0]
        cur.close()
    return chat_history_json_path
