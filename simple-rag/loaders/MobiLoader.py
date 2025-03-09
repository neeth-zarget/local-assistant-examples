# MobiLoader.py
from langchain.schema import Document
import mobi

class MobiLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self):
        mobi_file = mobi.Mobi(self.file_path)
        mobi_file.parse()
        text = mobi_file.get_text()
        return [Document(page_content=text)]