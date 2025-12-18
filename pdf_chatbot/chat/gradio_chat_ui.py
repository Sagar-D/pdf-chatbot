import gradio as gr
import pdf_chatbot.config as config


def _disable_inputs(msg: str):
    return (
        msg,
        gr.update(interactive=False),
        gr.update(
            value="",
            placeholder="Processing your request… please wait",
            interactive=False,
        ),
        gr.update(interactive=False),
        gr.update(interactive=False),
    )


def _enable_inputs():
    return (
        gr.update(interactive=True),
        gr.update(value="", placeholder="Type your query here...", interactive=True),
        gr.update(interactive=True),
        gr.update(interactive=True),
    )


def create_gradio_chat_interface(fn):

    with gr.Blocks() as app:
        chatbot = gr.Chatbot(height=450)
        msg_state = gr.State()

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
            fn=_disable_inputs,
            inputs=[msg],
            outputs=[msg_state, llm_platform, msg, files, send],
        ).then(fn=fn, inputs=[msg_state, files, llm_platform], outputs=[chatbot]).then(
            fn=_enable_inputs, inputs=[], outputs=[llm_platform, msg, files, send]
        )
        msg.submit(
            fn=_disable_inputs,
            inputs=[msg],
            outputs=[msg_state, llm_platform, msg, files, send],
        ).then(fn=fn, inputs=[msg_state, files, llm_platform], outputs=[chatbot]).then(
            fn=_enable_inputs, inputs=[], outputs=[llm_platform, msg, files, send]
        )

    return app
