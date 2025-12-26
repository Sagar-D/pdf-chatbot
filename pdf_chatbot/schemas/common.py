from pydantic import BaseModel, Field
from enum import Enum


class ErrorCode(str, Enum):
    UNAUTHORIZED = "UNAUTHORIZED"
    BAD_REQUEST = "BAD_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class APIStatus(str, Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class APIErrorData(BaseModel):
    code: ErrorCode
    message: str


class ErrorResponse(BaseModel):
    status: str = "ERROR"
    error: APIErrorData

    @classmethod
    def from_data(cls, error_code: ErrorCode, error_message: str) -> "ErrorResponse":
        return cls(error=APIErrorData(code=error_code, message=error_message))
