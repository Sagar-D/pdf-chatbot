from pdf_chatbot.db import repository
from passlib.context import CryptContext
from pdf_chatbot import config
import json
from pathlib import Path


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_account(username: str, password: str) -> int:

    user_id = repository.insert_user(username, hash_password(password))

    user_chat_history_path = f"{config.CHAT_HISTORY_ROOT_FOLDER}user_{user_id}.json"
    file_path = Path(user_chat_history_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as chat_file:
        json.dump([], chat_file)

    repository.insert_user_chat_history(user_id, user_chat_history_path)
    return user_id


def authenticate_and_get_user(username: str, password: str) -> dict | None:

    if not username or not password:
        raise ValueError("Required params 'username' or 'password' is missing")

    user = repository.get_user(username)
    if not user:
        return None
    if not verify_password(password=password, password_hash=user["password_hash"]):
        return None
    return user
