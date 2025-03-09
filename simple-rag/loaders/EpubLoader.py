# epub_loader.py
import ebooklib
from ebooklib import epub
from langchain.schema import Document

class EpubLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self):
        book = epub.read_epub(self.file_path)
        items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
        documents = []

        for item in items:
            content = item.get_body_content().decode('utf-8')
            documents.append(Document(page_content=content))

        return documents