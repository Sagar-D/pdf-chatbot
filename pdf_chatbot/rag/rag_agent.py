from langgraph.graph import StateGraph, END
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, Field
from typing import TypedDict, Union

import pdf_chatbot.llm.prompt_templates as PromptTemplates
from pdf_chatbot.llm.model_manager import get_llm_instance
from pdf_chatbot.documents.document_processor import DocumentProcessor
from pdf_chatbot.rag.retriever import Retriever


class RAGAgentState(TypedDict):
    input: str
    files: list[str]
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

    def _ingest_knowledge(self, state: RAGAgentState) -> RAGAgentState:
        file_paths = state["files"]
        doc_processor = DocumentProcessor()
        doc_processor.store_docs_to_db(file_paths=file_paths)
        return state

    def _enrich_query_for_retreival(self, state: RAGAgentState) -> RAGAgentState:
        state["enriched_query"] = ""

        class EnrichedQuery(BaseModel):
            enriched_query: str = Field(
                description="Enriched user query for a better (semantic + keyword) RAG retreival"
            )

        chain = PromptTemplates.QUERY_ENRICHMENT_PROMPT | get_llm_instance(
            state["llm_platform"]
        ).with_structured_output(EnrichedQuery)
        response: EnrichedQuery = chain.invoke(state)
        state["enriched_query"] = response.enriched_query.strip()
        print(f"ENRICHED QUERY : {state['enriched_query']}")
        print(f"ORIGINAL QUERY : {state['input']}")
        return state

    def _get_context(self, state: RAGAgentState) -> RAGAgentState:
        self.retriever = Retriever()
        state["context_docs"] = self.retriever.query_docs(state["enriched_query"])
        state["context"] = "\n\n".join(
            [doc.page_content for doc in state["context_docs"]]
        )
        return state

    def _is_answerable(self, state: RAGAgentState) -> bool:

        if ("context" not in state) or (state["context"].strip() == ""):
            state["error"] = (
                "Couldn't find any relevent document to answer user query. Please try with different query"
            )
            state["messages"].append(AIMessage(state["error"]))
            return False

        class IsEligibleResponse(BaseModel):
            is_answerable: bool = Field(
                "Boolean field representing whether the user query can be answered using provided context or not"
            )

        chain = PromptTemplates.QUERY_ELIGIBILITY_PROMPT | get_llm_instance(
            state["llm_platform"]
        ).with_structured_output(IsEligibleResponse)
        response: IsEligibleResponse = chain.invoke(state)
        if not response.is_answerable:
            state["error"] = (
                "The user query is not related to any of the documents provided. Please try with differnt query"
            )
            state["messages"].append(AIMessage(state["error"]))
        return response.is_answerable

    def _answer_user_query(self, state: RAGAgentState) -> RAGAgentState:

        class QueryAnswerResponse(BaseModel):
            reasons: list[str] = Field(
                description="Reasons why you think the provided answer is relevent to user query."
            )
            context_references: list[str] = Field(
                description="References to the context on which you have rooted your answers."
            )
            answer: str = Field(
                description="Answer to the user query based on provided context."
            )

        chain = PromptTemplates.ANSWER_USER_QUERY_PROMPT | get_llm_instance(
            state["llm_platform"]
        ).with_structured_output(QueryAnswerResponse)
        response = chain.invoke(state)
        state["messages"].append(AIMessage(content=response.answer))
        return state

    def _compile_graph(self):

        graph = StateGraph(RAGAgentState)
        graph.add_node("ingest_knowledge", self._ingest_knowledge)
        graph.add_node("enrich_query", self._enrich_query_for_retreival)
        graph.add_node("get_context", self._get_context)
        graph.add_node("answer_user_query", self._answer_user_query)

        graph.set_entry_point("ingest_knowledge")
        graph.add_edge("ingest_knowledge", "enrich_query")
        graph.add_edge("enrich_query", "get_context")
        graph.add_conditional_edges(
            "get_context",
            self._is_answerable,
            {False: END, True: "answer_user_query"},
        )
        graph.add_edge("answer_user_query", END)
        self.app = graph.compile()
        print(self.app.get_graph().draw_ascii())

    def invoke(self, state: RAGAgentState) -> RAGAgentState:

        if (
            ("input" not in state)
            or (type(state["input"]) != str)
            or state["input"].strip() == ""
        ):
            raise ValueError("Missing required attribute 'input' in state object")
        if (
            ("files" not in state)
            or (type(state["files"]) != list)
            or len(state["files"]) == 0
        ):
            raise ValueError("Missing required attribute 'files' in state object")

        state["llm_platform"] = state.get("llm_platform") or "ollama"
        state["messages"] = state.get("messages") or []
        state["messages"].append(HumanMessage(state["input"]))

        return self.app.invoke(state)
