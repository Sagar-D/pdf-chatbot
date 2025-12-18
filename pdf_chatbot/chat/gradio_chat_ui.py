import gradio as gr
import pdf_chatbot.config as config


def _gradio_pre_processing(state: dict, msg: str, llm_platform: str):
    state = state or {}
    if msg:
        state["input"] = msg
    if llm_platform:
        state["llm_platform"] = llm_platform
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


def _gradia_post_processing():
    return (
        gr.update(interactive=True),
        gr.update(value="", placeholder="Type your query here...", interactive=True),
        gr.update(interactive=True),
        gr.update(interactive=True),
    )


def create_gradio_chat_interface(chat_fn):

    with gr.Blocks() as app:
        chatbot = gr.Chatbot(height=450)
        state = gr.State({})

        with gr.Row():
            llm_platform = gr.Dropdown(
                choices=config.LLM_PLATFORMS,
                value=config.LLM_PLATFORMS[0],
                type="value",
                multiselect=False,
            )
            msg = gr.Textbox(placeholder="Type your query here...", scale=8)
            files = gr.File(
                file_count="multiple", type="binary", file_types=[".pdf"], height=80
            )
            send = gr.Button("Send", scale=1)

        send.click(
            fn=_gradio_pre_processing,
            inputs=[state, msg, llm_platform],
            outputs=[state, llm_platform, msg, files, send],
        ).then(fn=chat_fn, inputs=[state, files], outputs=[state, chatbot]).then(
            fn=_gradia_post_processing,
            inputs=[],
            outputs=[llm_platform, msg, files, send],
        )
        msg.submit(
            fn=_gradio_pre_processing,
            inputs=[state, msg, llm_platform],
            outputs=[state, llm_platform, msg, files, send],
        ).then(fn=chat_fn, inputs=[state, files], outputs=[state, chatbot]).then(
            fn=_gradia_post_processing,
            inputs=[],
            outputs=[llm_platform, msg, files, send],
        )

    return app
