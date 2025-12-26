from pydantic import BaseModel, UUID4
from pdf_chatbot.schemas.common import APIStatus


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginData(BaseModel):
    session_uuid: UUID4


class LoginResponse(BaseModel):
    status: APIStatus = APIStatus.SUCCESS
    data: LoginData

    @classmethod
    def from_data(cls, session_uuid: UUID4) -> "LoginResponse":
        return cls(data= LoginData(session_uuid=session_uuid))


class LogoutData(BaseModel):
    message: str = "Logged out successfully"


class LogoutResponse(BaseModel):
    status: APIStatus = APIStatus.SUCCESS
    data: LogoutData = LogoutData()

