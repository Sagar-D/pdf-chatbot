from docling.document_converter import DocumentConverter


class DocumentProcessor:

    def __init__(self):
        pass

    def convert_to_markdown(self, file_paths: list[str]):

        doc_converter = DocumentConverter()
        markdown_docs = []
        for file_path in file_paths :
            result = doc_converter.convert(source=file_path)
            markdown = result.document.export_to_markdown()
            markdown_docs.append(markdown)
        return markdown_docs
    
    def chunk_mardown_docs


if __name__ == "__main__":

    file_path = "/Users/sagard/Downloads/test_docling.pdf"
    doc_processor = 
    markdown = 
