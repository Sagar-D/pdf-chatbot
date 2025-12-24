from pdf_chatbot.chat.chat_handler import ChatHandler
from pdf_chatbot.chat.gradio_chat_ui import create_gradio_chat_interface
from pdf_chatbot.user.session import get_session_by_user_id

# Replace once Session Management is complete
session = get_session_by_user_id(1)

chat_handler = ChatHandler(session)
app = create_gradio_chat_interface(chat_handler.chat)
app.launch()
