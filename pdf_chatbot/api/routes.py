from fastapi import FastAPI, Header, Body, status, Depends
from fastapi.exceptions import HTTPException
from contextlib import asynccontextmanager
from pydantic import UUID4
from typing import Annotated
import base64
import binascii

from pdf_chatbot.user.account import create_account, authenticate_and_get_user
from pdf_chatbot.user.session import session_manager
from pdf_chatbot.chat.chat_handler import smart_chat
from pdf_chatbot.db import setup
from pdf_chatbot.schemas.auth import LoginRequest, LoginResponse, LogoutResponse
from pdf_chatbot.schemas.common import ErrorResponse, ErrorCode
from pdf_chatbot.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse
from pdf_chatbot.errors.document_error import DocumentError, InvalidDocumentError
from pdf_chatbot.errors.rag_agent_error import RAGAgentError
from pdf_chatbot.api.error_handlers import (
    document_error_handler,
    rag_agent_error_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup.setup_chat_history()
    setup.initialize_db()
    yield


app = FastAPI(lifespan=lifespan)
app.add_exception_handler(DocumentError, document_error_handler)
app.add_exception_handler(RAGAgentError, rag_agent_error_handler)


async def authentication_layer(
    session_id: Annotated[UUID4, Header(alias="X-Session-UUID")],
):
    session = session_manager.get_session(session_id=str(session_id))
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse.from_data(
                error_code=ErrorCode.UNAUTHORIZED,
                error_message="Unauthorized User.",
            ).model_dump(),
        )
    return session


@app.post(path="/account/signup")
def user_signup(user_data: Annotated[LoginRequest, Body()]) -> LoginResponse:
    user_id = create_account(username=user_data.username, password=user_data.password)
    session_id = session_manager.create_session(user_id=user_id)
    return LoginResponse.from_data(session_uuid=session_id)


@app.post(path="/account/login")
def user_login(
    req_body: Annotated[LoginRequest, Body()],
) -> LoginResponse | ErrorResponse:
    user = authenticate_and_get_user(
        username=req_body.username, password=req_body.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse.from_data(
                error_code=ErrorCode.UNAUTHORIZED,
                error_message="Incorrect UserID or Password.",
            ).model_dump(),
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
    session: Annotated[dict, Depends(authentication_layer)],
) -> ChatHistoryResponse | ErrorResponse:
    return ChatHistoryResponse.from_data(chat_history=session["chat_history"])


@app.post("/chat")
async def chat(
    chat_request: ChatRequest,
    session: Annotated[dict, Depends(authentication_layer)],
) -> ChatResponse | ErrorResponse:

    binary_files = []
    for file in chat_request.files:
        try:
            encoded_bytes = file.file_content_base64.encode("utf-8")
            binary_files.append(base64.b64decode(encoded_bytes, validate=True))
        except (ValueError, binascii.Error):
            raise InvalidDocumentError(
                f"Invalid base64 encoding for file '{file.file_name}'"
            )
    chat_thread = await smart_chat(
        session=session,
        input=chat_request.message,
        files=binary_files,
        agent_config=chat_request.agent_config,
    )
    session["chat_history"] = chat_thread
    return ChatResponse.from_data(chat_thread=chat_thread)
