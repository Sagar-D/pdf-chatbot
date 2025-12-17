from pdf_chatbot.rag.rag_agent import RAGAgent, RAGAgentState
from langchain.messages import AIMessage, HumanMessage
from typing import Union
import gradio as gr

class ChatHandler:

    def __init__(self):
        self.agent = RAGAgent()
        self.agent_state: RAGAgentState = {
            "input": "",
            "messages": [],
            "files": [],
        }

    def chat(self, query: str, files: list[str], llm_platform: str):

        query = query or ""
        files = files or []
        llm_platform = llm_platform or self.agent_state.get("llm_platform") or "ollama"

        if query.strip() == "":
            raise gr.Error("Please enter a User query in the input box")
        if len(self.agent_state["files"]) == 0 and len(files) == 0:
            raise gr.Error(
                "Value Error: No PDF file uploaded. Please attach a PDF file"
            )

        if len(files) > 0:
            self.agent_state["files"] = files
        self.agent_state["input"] = query
        self.agent_state["llm_platform"] = llm_platform

        self.agent_state = self.agent.invoke(self.agent_state)
        return self._generate_gradio_chat(self.agent_state["messages"])

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