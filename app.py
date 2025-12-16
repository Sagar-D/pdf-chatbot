from agent import PDFAgent
from langchain.messages import AIMessage

file_paths = [
    "/Users/sagard/Downloads/test_docling.pdf",
    "/Users/sagard/Downloads/iphone17.pdf",
    "/Users/sagard/Downloads/india_press_note.pdf",
]
agent = PDFAgent()

while True:

    query = input("User Query : ")
    result = agent.invoke({"input": query, "files": file_paths})

    for error in result["errors"]:
        print("--" * 40)
        print(f"Error : {error}")
        print("--" * 40)
    if len(result["messages"]) > 0 and type(result["messages"][-1]) == AIMessage:
        print(result["messages"][-1].pretty_print())
