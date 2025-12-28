import gradio as gr
from langchain_core.messages import AIMessage, HumanMessage
import pdf_chatbot.config as config
from pdf_chatbot.chat.chat_handler import smart_chat
from pdf_chatbot.errors.base import PDFChatbotError
from pdf_chatbot.db.repository import get_user
from pdf_chatbot.schemas.agent import AgentConfig


def _format_messages_to_gradio_chat(
    messages: list[AIMessage | HumanMessage],
) -> list[dict]:
    formatted_messages = []
    for message in messages:
        if type(message) == AIMessage:
            formatted_messages.append({"role": "assistant", "content": message.content})
        elif type(message) == HumanMessage:
            formatted_messages.append({"role": "user", "content": message.content})
    return formatted_messages


def _format_messages_to_langchain(
    messages: list[dict],
) -> list[AIMessage | HumanMessage]:
    formatted_messages = []
    for message in messages:
        if str(message["role"]) == "user":
            formatted_messages.append(HumanMessage(content=message["content"]))
        elif str(message["role"]) == "assistant":
            formatted_messages.append(AIMessage(content=message["content"]))
    return formatted_messages


def _gradio_pre_processing(
    state: dict,
    user: str,
    llm_platform: str,
    msg: str,
    chat_history: list[dict],
    q_enrich: bool,
):
    state = state or {}
    if msg:
        state["input"] = msg
    if user:
        state["user"] = user
    state["chat_history"] = chat_history or []
    state["llm_platform"] = llm_platform or config.DEFAULT_LLM_PLATFORM
    state["query_enrichment_enabled"] = q_enrich
    state.pop("error", None)

    return (
        state,
        gr.update(interactive=False),
        gr.update(
            value="",
            placeholder="Processing your request… please wait",
            interactive=False,
        ),
        gr.update(interactive=False),
        gr.update(interactive=False),
        gr.update(interactive=False),
    )


async def warn_and_return(gr_state: dict, msg: str):
    gr.Warning(msg)
    gr_state["error"] = "ERROR"
    return gr_state, gr_state["chat_history"]


async def gradio_chat(state: dict, files: list[bytes] | None = None):

    if (not state.get("input")) or state.get("input").strip() == "":
        return warn_and_return(state, "Please enter a User query in the input box")
    if (not state.get("user")) or state.get("user").strip() == "":
        return warn_and_return(
            state, "Please select a valid username from the dropdown."
        )

    user_obj = get_user(username=state["user"])
    if not user_obj:
        return warn_and_return(
            state, "Unaotherised User. Selected user doesn't have valid access."
        )
    chat_session = {
        "user_id": user_obj["user_id"],
        "chat_history": _format_messages_to_langchain(state["chat_history"]),
    }
    try:
        state["chat_history"] = await smart_chat(
            chat_session,
            input=state["input"],
            files=files,
            agent_config=AgentConfig(
                llm_platform=state["llm_platform"],
                query_enrichment_enabled=state["query_enrichment_enabled"],
            ),
        )
    except PDFChatbotError as e:
        gr.Warning(str(e))
        state["error"] = "PDF_CHATBOT_ERROR"
        return state, state["chat_history"]

    return state, _format_messages_to_gradio_chat(state["chat_history"])


def _gradio_post_processing(state: dict):

    msg_value = state.get("input") if state.get("error") else ""
    state.pop("input", None)
    state.pop("error", None)
    return (
        gr.update(interactive=True),
        gr.update(
            value=msg_value, placeholder="Type your query here...", interactive=True
        ),
        gr.update(interactive=True),
        gr.update(interactive=True),
        gr.update(interactive=True),
    )


def _hadle_chat_mode_label(files: list[str]):

    if files and type(files) == list and len(files) > 0:
        return gr.update(visible=True)
    return gr.update(visible=False)


def create_gradio_chat_interface():

    with gr.Blocks() as app:

        gr_state = gr.State({})
        with gr.Row():
            chatbot = gr.Chatbot(height=450, scale=10)
            with gr.Column():
                with gr.Row():
                    chat_mode = gr.Markdown(value="RAG Agent Configs / Feature flags")
                with gr.Row():
                    q_enrich = gr.Checkbox(value=True, label="Enable Query Enrichment")

        with gr.Row():
            chat_mode = gr.Markdown(
                value="🔒 Document-Grounded Mode Enabled", visible=False
            )

        with gr.Row():

            user = gr.Dropdown(
                choices=["demo"],
                value="demo",
                type="value",
                label="User",
                multiselect=False,
                visible=False,
            )
            llm_platform = gr.Dropdown(
                choices=config.LLM_PLATFORMS,
                value=config.DEFAULT_LLM_PLATFORM,
                type="value",
                label="LLM Platform",
                multiselect=False,
            )
            msg = gr.Textbox(
                placeholder="Type your query here...", label="User Message:", scale=8
            )
            files = gr.File(
                file_count="multiple",
                type="binary",
                file_types=[".pdf"],
                height=80,
            )
            send = gr.Button("Send")

        files.change(
            fn=_hadle_chat_mode_label,
            inputs=[files],
            outputs=[chat_mode],
        )

        send.click(
            fn=_gradio_pre_processing,
            inputs=[gr_state, user, llm_platform, msg, chatbot, q_enrich],
            outputs=[gr_state, llm_platform, msg, user, send],
        ).then(
            fn=gradio_chat, inputs=[gr_state, files], outputs=[gr_state, chatbot]
        ).then(
            fn=_gradio_post_processing,
            inputs=[gr_state],
            outputs=[llm_platform, msg, user, send, q_enrich],
        )
        msg.submit(
            fn=_gradio_pre_processing,
            inputs=[gr_state, user, llm_platform, msg, chatbot, q_enrich],
            outputs=[gr_state, llm_platform, msg, user, send, q_enrich],
        ).then(
            fn=gradio_chat, inputs=[gr_state, files], outputs=[gr_state, chatbot]
        ).then(
            fn=_gradio_post_processing,
            inputs=[gr_state],
            outputs=[llm_platform, msg, user, send, q_enrich],
        )

    return app
