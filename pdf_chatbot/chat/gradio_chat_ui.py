import gradio as gr
import pdf_chatbot.config as config


def create_graido_chat_interface(fn):

    with gr.Blocks() as app:
        chatbot = gr.Chatbot(height=450)

        with gr.Row():
            llm_platform = gr.Dropdown(
                choices=config.LLM_PLATFORM_CHOICES,
                value=config.LLM_PLATFORM_CHOICES[0],
                type="value",
                multiselect=False,
            )
            msg = gr.Textbox(placeholder="Type your query here...", scale=8)
            files = gr.File(
                file_count="multiple", type="filepath", file_types=[".pdf"], height=80
            )
            send = gr.Button("Send", scale=1)

        send.click(fn=fn, inputs=[msg, files, llm_platform], outputs=[chatbot])
        msg.submit(fn=fn, inputs=[msg, files, llm_platform], outputs=[chatbot])
    
    return app
