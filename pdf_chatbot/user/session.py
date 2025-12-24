_session = {
    "session_1": {
        "user_id": 1,
        "chat_history": [],
        "active_docs": [],
        "created_at": "",
        "last_active_at": ""
    }
}
_session_by_user_id = {
    1: "session_1"
}

def get_session(session_id: str) :
    return _session.get(session_id)

def get_session_by_user_id(user_id: int) :
    session_id = _session_by_user_id.get(user_id)
    return _session.get(session_id) if session_id else None

def create_session(user_id:int) :
    return _session_by_user_id.get(user_id)

def delete_session(session_id:str) :
    current_session = _session.get(session_id)
    _session.pop(session_id)
    _session_by_user_id.pop(current_session.get("user_id"))
    pass


if __name__ == "__main__" :

    user_id = 1
    session_id = create_session(user_id)
    print("....Created the user session...")
    print(f"Session : {get_session(session_id)}")
    print(f"Session by user id : {get_session_by_user_id(user_id)}")
    delete_session(session_id)
    print("....Deleted the user session...")
    print(f"Session : {get_session(user_id)}")
    print(f"Session by user id : {get_session_by_user_id(user_id)}")