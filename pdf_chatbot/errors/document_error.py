from pdf_chatbot.errors.base import PDFChatbotError


class DocumentError(PDFChatbotError):
    """Base class for document-related errors."""
    pass


class InvalidDocumentError(DocumentError):
    """Invalid, corrupt, or unsupported document."""
    pass


class DocumentConversionError(DocumentError):
    """PDF could not be converted to text."""
    pass


class DocumentChunkingError(DocumentError):
    """Document could not be chunked."""
    pass
