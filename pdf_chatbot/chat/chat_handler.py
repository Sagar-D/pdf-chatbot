from pdf_chatbot.rag.rag_agent import RAGAgent, RAGAgentState
from pdf_chatbot.documents.document_processor import DocumentProcessor
from langchain.messages import AIMessage, HumanMessage
from typing import Union
import gradio as gr
from pdf_chatbot import config


class ChatHandler:

    def __init__(self):
        self.agent = RAGAgent()

    def chat(self, state: dict, files: list[bytes]):

        state = state or {}
        files = files or []
        state["messages"] = state.get("messages") or []
        state["llm_platform"] = state.get("llm_platform") or config.LLM_PLATFORMS[0]

        if (not state.get("input")) or state.get("input").strip() == "":
            gr.Warning("Please enter a User query in the input box")
            return state, self._generate_gradio_chat(state["messages"])
        if len(files) == 0:
            gr.Warning("No PDF file uploaded. Please attach a PDF file")
            return state, self._generate_gradio_chat(state["messages"])

        if len(files) > 0:
            self._ingest_knowledge(files)

        state = self.agent.invoke(state)
        return state, self._generate_gradio_chat(state["messages"])

    def _generate_gradio_chat(
        self, messages: list[Union[AIMessage, HumanMessage]]
    ) -> list[dict]:

        history = []
        for message in messages:
            if type(message) == AIMessage:
                role = "assistant"
            elif type(message) == HumanMessage:
                role = "user"
            else:
                continue
            history.append({"role": role, "content": message.content})
        return history

    def _ingest_knowledge(self, files: list[bytes]):
        DocumentProcessor().store_docs_to_db(files)
