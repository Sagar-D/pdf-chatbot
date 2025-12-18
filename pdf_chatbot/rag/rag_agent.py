from langgraph.graph import StateGraph, END
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from typing import TypedDict, Union

import pdf_chatbot.llm.prompt_templates as PromptTemplates
from pdf_chatbot.llm.model_manager import get_llm_instance
from pdf_chatbot.documents.document_processor import DocumentProcessor
from pdf_chatbot.rag.retriever import Retriever
import pdf_chatbot.config as config


class RAGAgentState(TypedDict):
    input: str
    messages: list[Union[AIMessage, HumanMessage, ToolMessage]]
    error: str
    enriched_query: str
    context_docs: list[str]
    context: str
    llm_platform: str


class RAGAgent:

    def __init__(self):
        self.graph = StateGraph(RAGAgentState)
        self._compile_graph()

    def _enrich_query_for_retreival(self, state: RAGAgentState) -> RAGAgentState:

        if not config.PROMPT_ENRICHMENT_FEATURE_ENABLED:
            state["enriched_query"] = state["input"]
            return state

        chain = (
            PromptTemplates.QUERY_ENRICHMENT_PROMPT
            | get_llm_instance(
                platform=state["llm_platform"],
                model=config.QUERY_ENRICHMENT_MODEL[state["llm_platform"]],
            )
            | StrOutputParser()
        )
        enriched_query = chain.invoke(state)
        state["enriched_query"] = enriched_query
        return state

    def _get_context(self, state: RAGAgentState) -> RAGAgentState:
        self.retriever = Retriever()
        state["context_docs"] = self.retriever.query_docs(state["enriched_query"], k=3)
        state["context"] = "\n\n".join(
            [doc.page_content for doc in state["context_docs"]]
        )
        return state

    def _is_respondable(self, state: RAGAgentState) -> bool:

        if ("context" not in state) or (state["context"].strip() == ""):
            state["error"] = (
                "Couldn't find any relevent document to answer user query. Please try with different query"
            )
            state["messages"].append(AIMessage(state["error"]))
            return False
        return True

    def _respond_to_user_query(self, state: RAGAgentState) -> RAGAgentState:

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

        chain = PromptTemplates.RESPOND_WITH_EVIDENCE_PROMPT | get_llm_instance(
            platform=state["llm_platform"],
            model=config.RESPONSE_GENERATOR_MODEL[state["llm_platform"]],
        ).with_structured_output(QueryResponse)

        prompt_inputs = {
            "input": state["enriched_query"],
            "context": state["context"],
            "messages": [],
        }

        if config.IS_CONVERSATIONAL_RAG:
            prompt_inputs["messages"] = state["messages"]
            prompt_inputs["input"] = state["input"]

        response: QueryResponse = chain.invoke(state)
        if response.is_evidence_based:
            state["messages"].append(AIMessage(content=response.response))
        else:
            state["error"] = (
                "The user query is not related to any of the documents provided. Please try with differnt query"
            )
            state["messages"].append(AIMessage(state["error"]))
        return state

    def _compile_graph(self):

        graph = StateGraph(RAGAgentState)
        graph.add_node("enrich_query", self._enrich_query_for_retreival)
        graph.add_node("get_context", self._get_context)
        graph.add_node("respond_to_user_query", self._respond_to_user_query)

        graph.set_entry_point("enrich_query")
        graph.add_edge("enrich_query", "get_context")
        graph.add_conditional_edges(
            "get_context",
            self._is_respondable,
            {False: END, True: "respond_to_user_query"},
        )
        graph.add_edge("respond_to_user_query", END)
        self.app = graph.compile()
        print(self.app.get_graph().draw_ascii())

    def invoke(self, state: RAGAgentState) -> RAGAgentState:

        if (
            ("input" not in state)
            or (type(state["input"]) != str)
            or state["input"].strip() == ""
        ):
            raise ValueError("Missing required attribute 'input' in state object")

        state["llm_platform"] = state.get("llm_platform") or "ollama"
        state["messages"] = state.get("messages") or []
        state["messages"].append(HumanMessage(state["input"]))

        return self.app.invoke(state)
