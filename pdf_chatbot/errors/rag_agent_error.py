from pdf_chatbot.errors.base import PDFChatbotError


class RAGAgentError(PDFChatbotError):
    """Base class for RAG agent failures."""

    pass


class LLMServiceError(RAGAgentError):
    """LLM failed to respond or is unavailable."""

    def __init__(self, message="LLM service timed out or is unavailable", *args):
        super().__init__(message, *args)
