from pdf_chatbot.chat.chat_handler import rag_chat
from pdf_chatbot.chat.gradio_chat_ui import create_gradio_chat_interface
from pdf_chatbot.api.routes import app
import argparse


parser = argparse.ArgumentParser()
parser.add_argument(
    "--demo",
    action="store_true",
    help="If flag is passed, the gradio demp app will be launched",
)
args = parser.parse_args()

if args.demo:
    gradio_app = create_gradio_chat_interface()
    gradio_app.launch()
