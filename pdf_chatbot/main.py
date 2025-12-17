from pdf_chatbot.chat.chat_handler import ChatHandler
from pdf_chatbot.chat.gradio_chat_ui import create_graido_chat_interface

chat_handler = ChatHandler()
app = create_graido_chat_interface(chat_handler.chat)
app.launch()
