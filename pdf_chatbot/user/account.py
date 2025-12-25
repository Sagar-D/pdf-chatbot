from user.session import create_session
from db import repository
from passlib.context import CryptContext
import json
from pathlib import Path
import config

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_account(username: str, password_hash: str) -> int:

    user_chat_history_path = f"{config.CHAT_HISTORY_ROOT_FOLDER}user_{user_id}.json"
    file_path = Path(user_chat_history_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as chat_file:
        json.dump([], chat_file)

    user_id = repository.insert_user(username, password_hash)
    repository.insert_user_chat_history(user_id, user_chat_history_path)
    session_id = create_session(user_id=user_id)
    return user_id, session_id


def authenticate_user(username: str, password: str) -> int | None:

    if not username or not password:
        raise ValueError("Required params 'username' or 'password' is missing")

    user = repository.get_user(username)
    if not user:
        return None

    if verify_password(password=password, password_hash=user["password_hash"]):
        return user["user_id"]
