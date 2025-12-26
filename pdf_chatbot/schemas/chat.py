from pydantic import BaseModel
from pdf_chatbot.schemas.common import APIStatus
from enum import Enum
from datetime import datetime
from langchain_core.messages import BaseMessage


class File(BaseModel):
    file_name: str
    file_content_base64: str


class ChatRequest(BaseModel):
    message: str
    files: list[File]


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: Role
    content: str


class AssistantResponse(BaseModel):
    content: str
    timestamp: datetime


class ChatData(BaseModel):
    assistant_response: AssistantResponse
    chat_history: list[ChatMessage]


class ChatResponse(BaseModel):
    status: APIStatus = APIStatus.SUCCESS
    data: list[ChatMessage]


class ChatHistoryResponse(BaseModel):
    status: APIStatus = APIStatus.SUCCESS
    data: list[ChatMessage]

    @classmethod
    def from_data(cls, chat_history: list[BaseMessage]) -> "ChatHistoryResponse":
        chat_history: list[ChatMessage] = []
        for message in chat_history:
            if message.type == "human":
                chat_history.append(
                    ChatMessage(role=Role.USER, content=message.content)
                )
            elif message.type == "ai" :
                chat_history.append(
                    ChatMessage(role=Role.ASSISTANT,content=message.content)
                )
        return cls(data = chat_history)
