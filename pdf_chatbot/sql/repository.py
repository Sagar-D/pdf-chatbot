import sqlite3
import config


def create_account(username: str, password_hash: str) -> int:

    if not username_available(username):
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
        cur.execute(
            """INSERT INTO user_chat_history (user_id, chat_json_path) values (?, ?) """,
            (user_id, f".chat_history/user_{user_id}.json"),
        )

        conn.commit()
        cur.close()
    return user_id


def username_available(username: str) -> bool:
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


def authenticate_and_get_user_id(username: str, password_hash: str) -> int | None:
    user_id = None
    with sqlite3.connect(config.RELATIONAL_DB_NAME) as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT user_id, password_hash from accounts where username like ?",
            (username,),
        )
        data = cur.fetchone()
        if data and len(data) == 2 and str(data[1]) == password_hash:
            user_id = data[0]
        conn.commit()
        cur.close()
    return user_id


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
