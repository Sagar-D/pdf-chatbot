from langgraph.graph import StateGraph, END
from typing import TypedDict, Union
from helpers.llm_manager import get_llm_instance
from helpers.prompt_manager import QUERY_ELIGIBILITY_PROMPT, ANSWER_USER_QUERY_PROMPT
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from helpers.document_manager import DocumentProcessor
from helpers.retriever_manager import Retriever
from pydantic import BaseModel, Field


class PDFAgentState(TypedDict):
    input: str
    files: list[str]
    messages: list[Union[AIMessage, HumanMessage, ToolMessage]]
    errors: list[str]
    context_docs: list[str]
    context: str


class PDFAgent:

    def __init__(self):
        self.graph = StateGraph(PDFAgentState)
        self.llm = get_llm_instance()
        self._compile_graph()

    def _ingest_knowledge(self, state: PDFAgentState) -> PDFAgentState:
        file_paths = state["files"]
        doc_processor = DocumentProcessor()
        doc_processor.store_docs_to_db(file_paths=file_paths)
        return state

    def _get_context(self, state: PDFAgentState) -> PDFAgentState:
        self.retriever = Retriever()
        state["context_docs"] = self.retriever.query_docs(state["input"])
        state["context"] = "\n\n".join(
            [doc.page_content for doc in state["context_docs"]]
        )
        return state

    def _is_answerable(self, state: PDFAgentState) -> bool:

        if ("context" not in state) or (state["context"].strip() == ""):
            state["errors"].append(
                "Couldn't find any relevent document to answer user query"
            )
            return False

        class IsEligibleResponse(BaseModel):
            is_answerable: bool = Field(
                "Boolean field representing whether the user query can be answered using provided context or not"
            )

        chain = QUERY_ELIGIBILITY_PROMPT | self.llm.with_structured_output(
            IsEligibleResponse
        )
        response = chain.invoke(state)
        if not response.is_answerable:
            state["errors"].append(
                "The user query is not related to any of the documents provided. Please try with differnt query"
            )
        return response.is_answerable

    def _answer_user_query(self, state: PDFAgentState) -> PDFAgentState:

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

        chain = ANSWER_USER_QUERY_PROMPT | self.llm.with_structured_output(
            QueryAnswerResponse
        )
        response = chain.invoke(state)
        state["messages"].append(AIMessage(content=response.answer))
        return state

    def _compile_graph(self):

        graph = StateGraph(PDFAgentState)
        graph.add_node("ingest_knowledge", self._ingest_knowledge)
        graph.add_node("get_context", self._get_context)
        graph.add_node("answer_user_query", self._answer_user_query)

        graph.set_entry_point("ingest_knowledge")
        graph.add_edge("ingest_knowledge", "get_context")
        graph.add_conditional_edges(
            "get_context",
            self._is_answerable,
            {False: END, True: "answer_user_query"},
        )
        graph.add_edge("answer_user_query", END)
        self.app = graph.compile()
        print(self.app.get_graph().draw_ascii())

    def invoke(self, state: PDFAgentState) -> PDFAgentState:

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
        if (
            ("messages" not in state)
            or (type(state["messages"]) != list)
            or len(state["messages"]) == 0
        ):
            state["messages"] = [HumanMessage(state["input"])]
        if (
            ("errors" not in state)
            or (type(state["errors"]) != list)
            or len(state["errors"]) == 0
        ):
            state["errors"] = []

        return self.app.invoke(state)
