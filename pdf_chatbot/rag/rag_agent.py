from langgraph.graph import StateGraph, END
from langchain.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
import asyncio

from pdf_chatbot.schemas.agent import RAGAgentState
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


class RAGAgent:

    def __init__(self):
        self.graph = StateGraph(RAGAgentState)
        self._compile_graph()

    async def _enrich_query_for_retreival(self, state: RAGAgentState) -> RAGAgentState:

        if not state.config.query_enrichment_enabled:
            return state

        llm = None
        try:
            llm = await asyncio.wait_for(
                get_llm_instance_async(
                    platform=state.config.llm_platform,
                    model=config.QUERY_ENRICHMENT_MODEL[state.config.llm_platform],
                ),
                timeout=config.LLM_DEFAULT_TIMEOUT,
            )
        except asyncio.TimeoutError as e:
            raise LLMServiceError() from e

        enriched_query = None
        chain = PromptTemplates.QUERY_ENRICHMENT_PROMPT | llm | StrOutputParser()
        try:
            enriched_query = await asyncio.wait_for(
                chain.ainvoke({"messages": state.messages, "input": state.input}),
                timeout=config.LLM_DEFAULT_TIMEOUT,
            )
        except asyncio.TimeoutError as e:
            raise LLMServiceError() from e
        print(f"**** ENRICHED QUERY *** : {enriched_query}")
        return state.model_copy(update={"enriched_query": enriched_query})

    async def _get_context(self, state: RAGAgentState) -> RAGAgentState:

        metadata_filter = {
            "$and": [
                {"user_id": state.user_id},
                {"document_hash_id": {"$in": state.active_documents_hash_list}},
            ]
        }

        def retrieve_docs():
            retriever = ScopedHybridRetriever(metadata_filter=metadata_filter)
            query = state.enriched_query or state.input
            docs = retriever.query_docs(query=query, k=3)
            return docs

        retrieved_docs = await asyncio.to_thread(retrieve_docs)
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        return state.model_copy(update={"context": context})

    def _is_respondable(self, state: RAGAgentState) -> bool:

        if (not state.context) or (state.context.strip() == ""):
            return False
        return True

    async def _handle_no_context_error(self, state: RAGAgentState) -> RAGAgentState:
        return state.model_copy(
            update={
                "error": CONTEXT_NOT_AVAILABLE_ERROR_MESSAGE,
                "messages": [AIMessage(CONTEXT_NOT_AVAILABLE_ERROR_MESSAGE)],
            }
        )

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
                platform=state.config.llm_platform,
                model=config.RESPONSE_GENERATOR_MODEL[state.config.llm_platform],
            )
        except asyncio.TimeoutError as e:
            raise LLMServiceError() from e

        chain = (
            PromptTemplates.RESPOND_WITH_EVIDENCE_PROMPT
            | llm.with_structured_output(QueryResponse)
        )

        prompt_inputs = {
            "input": state.input,
            "context": state.context,
            "messages": state.messages,
        }

        try:
            response: QueryResponse = await asyncio.wait_for(
                chain.ainvoke(prompt_inputs), timeout=config.LLM_DEFAULT_TIMEOUT
            )
        except asyncio.TimeoutError as e:
            raise LLMServiceError() from e

        if response.is_evidence_based:
            return state.model_copy(
                update={"messages": [AIMessage(content=response.response)]}
            )
        else:
            return state.model_copy(
                update={
                    "messages": [AIMessage(CONTEXT_NOT_AVAILABLE_ERROR_MESSAGE)],
                    "error": CONTEXT_NOT_AVAILABLE_ERROR_MESSAGE,
                }
            )

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

        if state.input.strip() == "":
            raise ValueError("Missing required attribute 'input' in state object")

        state.messages.append(HumanMessage(state.input))
        return await self.app.ainvoke(state)
