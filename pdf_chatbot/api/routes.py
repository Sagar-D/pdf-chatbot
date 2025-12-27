from fastapi import FastAPI, Header, Body, Response, status
from pdf_chatbot.user.account import create_account, authenticate_and_get_user
from pdf_chatbot.user.session import session_manager
from pdf_chatbot.chat.chat_handler import smart_chat
from pydantic import UUID4
from typing import Annotated
import base64
from langchain_core.messages import messages_to_dict

from pdf_chatbot.schemas.auth import LoginRequest, LoginResponse, LogoutResponse
from pdf_chatbot.schemas.common import ErrorResponse, ErrorCode
from pdf_chatbot.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse

app = FastAPI()


@app.post(path="/account/signup")
def user_signup(user_data: Annotated[LoginRequest, Body()]) -> LoginResponse:
    user_id = create_account(username=user_data.username, password=user_data.password)
    session_id = session_manager.create_session(user_id=user_id)
    return LoginResponse.from_data(session_uuid=session_id)


@app.post(path="/account/login")
def user_login(
    req_body: Annotated[LoginRequest, Body()], response: Response
) -> LoginResponse | ErrorResponse:
    user = authenticate_and_get_user(
        username=req_body.username, password=req_body.password
    )
    if not user:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse.from_data(
            error_code=ErrorCode.UNAUTHORIZED,
            error_message="Incorrect UserID or Password.",
        )
    session_id = session_manager.create_session(user_id=user["user_id"])
    return LoginResponse.from_data(session_uuid=session_id)


@app.post(path="/account/logut")
def user_logout(
    session_id: Annotated[UUID4, Header(alias="X-Session-UUID")],
) -> LogoutResponse:
    session_manager.delete_session(session_id=str(session_id))
    return LogoutResponse()


@app.get("/chat/history")
def get_chat_history(
    session_id: Annotated[UUID4, Header(alias="X-Session-UUID")], response: Response
) -> ChatHistoryResponse | ErrorResponse:
    session = session_manager.get_session(session_id=str(session_id))
    if not session:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse.from_data(
            error_code=ErrorCode.UNAUTHORIZED,
            error_message="Unauthorized User.",
        )
    return ChatHistoryResponse.from_data(chat_history=session["chat_history"])


@app.post("/chat")
async def chat(
    chat_request: ChatRequest,
    response: Response,
    session_id: Annotated[UUID4, Header(alias="X-Session-UUID")],
    llm_platform: Annotated[str | None, Header(alias="LLM-Platform")] = None,
) -> ChatResponse | ErrorResponse:
    session = session_manager.get_session(session_id=str(session_id))
    if not session:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse.from_data(
            error_code=ErrorCode.UNAUTHORIZED,
            error_message="Unauthorized User.",
        )

    binary_files = []
    for file in chat_request.files:
        encoded_bytes = file.file_content_base64.encode("utf-8")
        binary_files.append(base64.b64decode(encoded_bytes))
    chat_thread = await smart_chat(
        session=session,
        input=chat_request.message,
        files=binary_files,
        llm_platform=llm_platform,
    )
    session["chat_history"] = chat_thread
    return ChatResponse.from_data(chat_thread=chat_thread)
