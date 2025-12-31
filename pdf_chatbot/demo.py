from pdf_chatbot.db import setup
from pdf_chatbot.chat.gradio_chat_ui import create_gradio_chat_interface
import os

port = int(os.getenv("PORT", 8080))
server = "0.0.0.0"

setup.setup_chat_history()
setup.initialize_db()


gradio_app = create_gradio_chat_interface()
gradio_app.queue(default_concurrency_limit=10)
gradio_app.launch(server_name=server, server_port=port)
