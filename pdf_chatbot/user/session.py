from db import repository
import json
from datetime import datetime
import uuid

_session = {
    "session_1": {
        "user_id": 1,
        "chat_history": [],
        "active_docs": [],
        "created_at": "",
        "last_active_at": "",
    }
}
_session_by_user_id = {1: "session_1"}


def get_session(session_id: str) -> dict:
    return _session.get(session_id)


def get_session_by_user_id(user_id: int) -> dict:
    session_id = _session_by_user_id.get(user_id)
    return _session.get(session_id) if session_id else None


def create_session(user_id: int, chat_history_file_path: str | None = None) -> dict:

    if not chat_history_file_path:
        chat_history_file_path = repository.get_user_chat_history(user_id=user_id)

    chat_history = []
    with open(chat_history_file_path, "r") as chat_file:
        chat_history = json.load(chat_file)

    current_session = {
        "user_id": user_id,
        "chat_history": chat_history,
        "active_docs": [],
        "created_at": datetime.now(),
        "last_active_at": datetime.now(),
    }
    session_id = str(uuid.uuid4())
    if _session_by_user_id.get(user_id) and _session.get(_session_by_user_id[user_id]):
        _session.pop(_session_by_user_id[user_id], None)

    _session[session_id] = current_session
    _session_by_user_id[user_id] = current_session
    return current_session


def delete_session(session_id: str):
    current_session = _session.get(session_id)
    _session.pop(session_id, None)
    _session_by_user_id.pop(current_session.get("user_id"), None)
    pass
