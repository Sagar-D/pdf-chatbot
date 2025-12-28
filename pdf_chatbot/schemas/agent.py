from pydantic import BaseModel, Field
from typing import Annotated
from langchain_core.messages import BaseMessage
from langchain_core.documents import Document
from langgraph.graph.message import add_messages
from pdf_chatbot import config


class AgentConfig(BaseModel):
    llm_platform: str = config.DEFAULT_LLM_PLATFORM
    query_enrichment_enabled: bool = config.QUERY_ENRICHMENT_FEATURE_ENABLED


class RAGAgentState(BaseModel):
    config: AgentConfig = AgentConfig()
    user_id: int
    input: str
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    enriched_query: str | None = None
    active_documents_hash_list: list[str]
    context: str | None = None
    error: str | None = None
