from gradio_app import create_graido_chat_interface
from chat_interface import ChatInterface

chatagent = ChatInterface()
app = create_graido_chat_interface(chatagent.chat)
app.launch()
