from pdf_chatbot.chat.gradio_chat_ui import create_gradio_chat_interface

gradio_app = create_gradio_chat_interface()
gradio_app.queue(default_concurrency_limit=10)
gradio_app.launch()
