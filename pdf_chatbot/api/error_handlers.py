from fastapi import Request
from fastapi.responses import JSONResponse

from pdf_chatbot.errors.document_error import DocumentError
from pdf_chatbot.errors.rag_agent_error import RAGAgentError
from pdf_chatbot.schemas.common import ErrorResponse, ErrorCode


def document_error_handler(request: Request, e: DocumentError):
    return JSONResponse(
        status_code=400,
        content={
            "detail": ErrorResponse.from_data(
                error_code=ErrorCode.BAD_REQUEST, error_message=str(e)
            ).model_dump()
        },
    )

def rag_agent_error_handler(request: Request, e: DocumentError):
    return JSONResponse(
        status_code=503,
        content={
            "detail": ErrorResponse.from_data(
                error_code=ErrorCode.BAD_REQUEST, error_message=f"Service Unavailable : {str(e)}"
            ).model_dump()
        },
    )
