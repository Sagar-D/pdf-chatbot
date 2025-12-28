from langgraph.graph import StateGraph, END, add_messages
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated
import asyncio
from functools import partial

import pdf_chatbot.llm.prompt_templates as PromptTemplates
from pdf_chatbot.llm.model_manager import get_llm_instance_async
from pdf_chatbot.rag.retriever import ScopedHybridRetriever
from pdf_chatbot.errors.rag_agent_error import LLMServiceError
import pdf_chatbot.config as config


CONTEXT_NOT_AVAILABLE_ERROR_MESSAGE = """\
I couldn’t find the answer in the uploaded document.

🔒 Document-Grounded Mode Enabled
When a PDF is uploaded, I generate responses strictly based on the document content only and do not use my general knowledge.

To proceed, you can:
- "rephrase your question"
- "upload a more relevant document"
- "or remove the document to allow a general answer"
"""


class RAGAgentState(TypedDict):
    user_id: str
    llm_platform: str
    input: str
    messages: Annotated[list[AIMessage | HumanMessage | ToolMessage], add_messages]
    enriched_query: str
    active_documents_hash_list: list[str]
    context_docs: list[str]
    context: str
    error: str


class RAGAgent:

    def __init__(self):
        self.graph = StateGraph(RAGAgentState)
        self._compile_graph()

    async def _enrich_query_for_retreival(self, state: RAGAgentState) -> RAGAgentState:

        if not config.PROMPT_ENRICHMENT_FEATURE_ENABLED:
            return {"enriched_query": state["input"]}

        llm = None
        try:
            llm = await asyncio.wait_for(
                get_llm_instance_async(
                    platform=state["llm_platform"],
                    model=config.QUERY_ENRICHMENT_MODEL[state["llm_platform"]],
                ),
                timeout=config.LLM_DEFAULT_TIMEOUT,
            )
        except asyncio.TimeoutError as e:
            raise LLMServiceError() from e

        enriched_query = None
        chain = PromptTemplates.QUERY_ENRICHMENT_PROMPT | llm | StrOutputParser()
        try:
            enriched_query = await asyncio.wait_for(
                chain.ainvoke(state), timeout=config.LLM_DEFAULT_TIMEOUT
            )
        except asyncio.TimeoutError as e:
            raise LLMServiceError() from e
        return {"enriched_query": enriched_query}

    async def _get_context(self, state: RAGAgentState) -> RAGAgentState:

        metadata_filter = {
            "$and": [
                {"user_id": state["user_id"]},
                {"document_hash_id": {"$in": state["active_documents_hash_list"]}},
            ]
        }

        def retrieve_docs():
            retriever = ScopedHybridRetriever(metadata_filter=metadata_filter)
            docs = retriever.query_docs(query=state["enriched_query"], k=3)
            return docs

        context_docs = await asyncio.to_thread(retrieve_docs)
        context = "\n\n".join([doc.page_content for doc in context_docs])
        return {"context_docs": context_docs, "context": context}

    def _is_respondable(self, state: RAGAgentState) -> bool:

        if ("context" not in state) or (state["context"].strip() == ""):
            return False
        return True

    async def _handle_no_context_error(self, state: RAGAgentState) -> RAGAgentState:
        return {
            "error": CONTEXT_NOT_AVAILABLE_ERROR_MESSAGE,
            "messages": [AIMessage(CONTEXT_NOT_AVAILABLE_ERROR_MESSAGE)],
        }

    async def _respond_to_user_query(self, state: RAGAgentState) -> RAGAgentState:

        class QueryResponse(BaseModel):
            is_evidence_based: bool = Field(
                description="Is your response rooted based on provided context"
            )
            evidences: list[str] = Field(
                description="References to the context on which you have rooted your response."
            )
            response: str = Field(
                description="Response to the user query based on provided context."
            )

        llm = None
        try:
            llm = await get_llm_instance_async(
                platform=state["llm_platform"],
                model=config.RESPONSE_GENERATOR_MODEL[state["llm_platform"]],
            )
        except asyncio.TimeoutError as e:
            raise LLMServiceError() from e

        chain = (
            PromptTemplates.RESPOND_WITH_EVIDENCE_PROMPT
            | llm.with_structured_output(QueryResponse)
        )

        prompt_inputs = {
            "input": state["enriched_query"],
            "context": state["context"],
            "messages": [],
        }

        if config.IS_CONVERSATIONAL_RAG:
            prompt_inputs["messages"] = state["messages"]
            prompt_inputs["input"] = state["input"]

        try:
            response: QueryResponse = await asyncio.wait_for(
                chain.ainvoke(prompt_inputs), timeout=config.LLM_DEFAULT_TIMEOUT
            )
        except asyncio.TimeoutError as e:
            raise LLMServiceError() from e

        if response.is_evidence_based:
            return {"messages": [AIMessage(content=response.response)]}
        else:
            return {
                "messages": [AIMessage(CONTEXT_NOT_AVAILABLE_ERROR_MESSAGE)],
                "error": CONTEXT_NOT_AVAILABLE_ERROR_MESSAGE,
            }

    def _compile_graph(self):

        graph = StateGraph(RAGAgentState)
        graph.add_node("enrich_query", self._enrich_query_for_retreival)
        graph.add_node("get_context", self._get_context)
        graph.add_node("respond_to_user_query", self._respond_to_user_query)
        graph.add_node("no_context_error_handler", self._handle_no_context_error)

        graph.set_entry_point("enrich_query")
        graph.add_edge("enrich_query", "get_context")
        graph.add_conditional_edges(
            "get_context",
            self._is_respondable,
            {True: "respond_to_user_query", False: "no_context_error_handler"},
        )
        graph.add_edge("respond_to_user_query", END)
        self.app = graph.compile()
        print(self.app.get_graph().draw_ascii())

    async def ainvoke(self, state: RAGAgentState) -> RAGAgentState:

        if (
            ("input" not in state)
            or (type(state["input"]) != str)
            or state["input"].strip() == ""
        ):
            raise ValueError("Missing required attribute 'input' in state object")

        if "user_id" not in state or type(state["user_id"]) != int:
            raise ValueError(
                "Missing or Invalid required attribute 'user_id' in state object"
            )

        state["llm_platform"] = state.get("llm_platform") or "ollama"
        state["messages"] = state.get("messages") or []
        state["messages"].append(HumanMessage(state["input"]))

        return await self.app.ainvoke(state)
