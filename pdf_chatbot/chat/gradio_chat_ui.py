import gradio as gr
from langchain_core.messages import AIMessage, HumanMessage
import pdf_chatbot.config as config
from pdf_chatbot.chat.chat_handler import smart_chat
from pdf_chatbot.db.repository import get_user


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
    state: dict, user: str, llm_platform: str, msg: str, chat_history: list[dict]
):
    state = state or {}
    if msg:
        state["input"] = msg
    if user:
        state["user"] = user
    state["chat_history"] = chat_history or []
    state["llm_platform"] = llm_platform or config.LLM_PLATFORMS[0]
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
    )


async def gradio_chat(state: dict, files: list[bytes] | None = None):

    if (not state.get("input")) or state.get("input").strip() == "":
        gr.Warning("Please enter a User query in the input box")
        state["error"] = "INVALID_PARAMS"
        return state, state["chat_history"]
    if (not state.get("user")) or state.get("user").strip() == "":
        gr.Warning("Please select a valid username from the dropdown.")
        state["error"] = "INVALID_PARAMS"
        return state, state["chat_history"]

    user_obj = get_user(username=state["user"])
    if not user_obj:
        gr.Warning("Unaotherised User. Selected user doesn't have valid access.")
        state["error"] = "UNAUTHORIZED"
        return state, state["chat_history"]
    chat_session = {
        "user_id": user_obj["user_id"],
        "chat_history": _format_messages_to_langchain(state["chat_history"]),
        "llm_platform": state["llm_platform"],
    }
    state["chat_history"] = await smart_chat(
        chat_session,
        input=state["input"],
        files=files,
        llm_platform=chat_session["llm_platform"],
    )
    return state, _format_messages_to_gradio_chat(state["chat_history"])


def _gradio_post_processing(state):

    msg_value = state.get("input") if state.get("error") else ""
    return (
        gr.update(interactive=True),
        gr.update(
            value=msg_value, placeholder="Type your query here...", interactive=True
        ),
        gr.update(interactive=True),
        gr.update(interactive=True),
    )


def _hadle_chat_mode_label(files: list[str]):

    if files and type(files) == list and len(files) > 0:
        return gr.update(visible=True)
    return gr.update(visible=False)


def create_gradio_chat_interface():

    with gr.Blocks() as app:
        chatbot = gr.Chatbot(height=450)
        state = gr.State({})

        with gr.Row():

            with gr.Column(scale=0):

                user = gr.Dropdown(
                    choices=["demo"],
                    value="demo",
                    type="value",
                    label="User",
                    multiselect=False,
                )
                llm_platform = gr.Dropdown(
                    choices=config.LLM_PLATFORMS,
                    value=config.LLM_PLATFORMS[0],
                    type="value",
                    label="LLM Platform",
                    multiselect=False,
                )
            with gr.Column(scale=8):
                msg = gr.Textbox(
                    placeholder="Type your query here...", label="User Message:"
                )
            with gr.Column(scale=0):
                chat_mode = gr.Markdown(
                    value="🔒 Document-Grounded Mode Enabled", visible=False
                )
                with gr.Row():
                    files = gr.File(
                        file_count="multiple",
                        type="binary",
                        file_types=[".pdf"],
                        height=80,
                    )
                    send = gr.Button("Send")

        files.change(
            fn=_hadle_chat_mode_label,
            inputs=[
                files,
            ],
            outputs=[
                chat_mode,
            ],
        )

        send.click(
            fn=_gradio_pre_processing,
            inputs=[state, user, llm_platform, msg, chatbot],
            outputs=[state, llm_platform, msg, user, send],
        ).then(fn=gradio_chat, inputs=[state, files], outputs=[state, chatbot]).then(
            fn=_gradio_post_processing,
            inputs=[state],
            outputs=[llm_platform, msg, user, send],
        )
        msg.submit(
            fn=_gradio_pre_processing,
            inputs=[state, user, llm_platform, msg, chatbot],
            outputs=[state, llm_platform, msg, user, send],
        ).then(fn=gradio_chat, inputs=[state, files], outputs=[state, chatbot]).then(
            fn=_gradio_post_processing,
            inputs=[state],
            outputs=[llm_platform, msg, user, send],
        )

    return app
