from pdf_chatbot.db import repository
from langchain_core.messages import messages_from_dict, messages_to_dict
from datetime import datetime
import json
import uuid


class _SessionManager:

    def __init__(self):
        self.sessions = {}
        self.sessions_by_user_id = {}

    def get_session(self, session_id: str) -> dict:
        return self.sessions.get(session_id)

    def get_session_id(self, user_id: int) -> str:
        return self.sessions_by_user_id.get(user_id)

    def getsessions_by_user_id(self, user_id: int) -> dict:
        session_id = self.sessions_by_user_id.get(user_id)
        return self.sessions.get(session_id) if session_id else None

    def create_session(
        self, user_id: int, chat_history_file_path: str | None = None
    ) -> dict:

        if self.sessions_by_user_id.get(user_id) and self.sessions.get(
            self.sessions_by_user_id[user_id]
        ):
            self.delete_session(self.sessions_by_user_id[user_id])

        if not chat_history_file_path:
            chat_history_file_path = repository.get_user_chat_history(user_id=user_id)

        chat_history_dict = []
        with open(chat_history_file_path, "r") as chat_file:
            chat_history_dict = json.load(chat_file)
        chat_history = messages_from_dict(chat_history_dict)

        session_id = str(uuid.uuid4())
        current_session = {
            "user_id": user_id,
            "chat_history": chat_history,
            "chat_history_file_path": chat_history_file_path,
            "active_docs": [],
            "created_at": datetime.now(),
            "last_active_at": datetime.now(),
        }
        self.sessions[session_id] = current_session
        self.sessions_by_user_id[user_id] = session_id
        return session_id

    def delete_session(self, session_id: str):
        current_session = self.sessions.get(session_id)
        if current_session:
            chat_history_dict = messages_to_dict(current_session["chat_history"])
            with open(current_session["chat_history_file_path"], "w") as chat_file:
                json.dump(chat_history_dict, chat_file, indent=2)
            self.sessions.pop(session_id, None)
            self.sessions_by_user_id.pop(current_session.get("user_id"), None)


session_manager = _SessionManager()
