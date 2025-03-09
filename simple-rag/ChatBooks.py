# ChatBooks.py
import datetime
import os

from langchain_core.globals import set_verbose, set_debug
from langchain_chroma import Chroma  # Updated import
from langchain_core.runnables import RunnableSequence
from langchain_ollama import ChatOllama  # Updated import
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain.schema.output_parser import StrOutputParser
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.runnable import RunnablePassthrough
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.prompts import ChatPromptTemplate

from config import Config
from helpers import get_processed_file_name
from loaders.EpubLoader import EpubLoader  # Import the custom EpubLoader
from icecream import ic

#from loaders.MobiLoader import MobiLoader

set_debug(True)
set_verbose(True)

class ChatBooks:
    vector_store = None
    retriever = None
    chain = None
    notes = {}
    local_model_path = "../../local_model"
    #embedding_function = FastEmbedEmbeddings(model_name=local_model_path)

    def __init__(self, llm_model: str = "qwen2.5"):
        self.model = ChatOllama(model=llm_model)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)
        self.prompt = ChatPromptTemplate([
            ("system", "You are a knowledgeable assistant who can answer questions and provide clarifications on the books uploaded by the user. You help users ask the right questions to understand more, provide additional references to build more knowledge, and offer insights across different books. Your responses should be informative, insightful, and helpful."),
            ("human", "Here are the document pieces: {context}\nQuestion: {question}"),
        ])

    def ingest(self, file_path: str):
        ic(file_path)

        processed_dir = Config.BOOKS_PROCESSED_DIR
        file_name = os.path.basename(file_path)
        processed_file_path = os.path.join(processed_dir, get_processed_file_name(file_name))

        if os.path.exists(processed_file_path):


            self.vector_store = Chroma(persist_directory="chroma_books_db", embedding_function=FastEmbedEmbeddings())
            self.qa_vector_store = Chroma(persist_directory="chroma_qa_db", embedding_function=FastEmbedEmbeddings())
            return  # Skip ingestion if the file is already processed

        if file_path.endswith(".pdf"):
            docs = PyPDFLoader(file_path=file_path).load()
        elif file_path.endswith(".epub"):
            docs = EpubLoader(file_path=file_path).load()
        elif file_path.endswith(".mobi"):
            docs = MobiLoader(file_path=file_path).load()
        else:
            return

        chunks = self.text_splitter.split_documents(docs)
        chunks = filter_complex_metadata(chunks)

        if not self.vector_store:
            self.vector_store = Chroma.from_documents(documents=chunks, embedding=FastEmbedEmbeddings(), persist_directory="chroma_books_db")
        else:
            self.vector_store.add_documents(documents=chunks)

        # Write the ingestion date to the processed file
        with open(processed_file_path, 'w') as f:
            f.write(f"Ingested on: {datetime.datetime.now().isoformat()}\n")

    def ask(self, query: str):
        if not self.vector_store:
            self.vector_store = Chroma(persist_directory="chroma_books_db", embedding_function=FastEmbedEmbeddings())
        if not self.qa_vector_store:
            self.qa_vector_store = Chroma(persist_directory="chroma_qa_db", embedding_function=FastEmbedEmbeddings())

        book_retriever = self.vector_store.as_retriever(search_type="similarity_score_threshold",
                                                        search_kwargs={"k": 10, "score_threshold": 0.0})
        qa_retriever = self.qa_vector_store.as_retriever(search_type="similarity_score_threshold",
                                                         search_kwargs={"k": 10, "score_threshold": 0.0})

        book_docs = book_retriever.invoke(query)
        qa_docs = qa_retriever.invoke(query)

        combined_docs = book_docs + qa_docs

        self.chain = (RunnablePassthrough()
                      | (lambda x: {"context": combined_docs, "question": query})
                      | self.prompt
                      | self.model
                      | StrOutputParser())

        if not self.chain:
            return "Please, add a document first."

        result = self.chain.invoke({"context": combined_docs, "question": query})
        references = ""
        references_text = "\n".join(references)
        return f"{result}\n\nReferences:\n{references_text}"

    def add_note_to_point(self, point_id: str, note: str):
        if point_id in self.notes:
            self.notes[point_id].append(note)
        else:
            self.notes[point_id] = [note]

    def store_qa(self, question: str, answer: str):
        qa_document = Document(page_content=f"Question: {question}\nAnswer: {answer}")
        qa_vector_store = Chroma.from_documents(documents=[qa_document], embedding=FastEmbedEmbeddings(), persist_directory="chroma_qa_db")

    def clear(self):
        self.vector_store = None
        self.retriever = None
        self.chain = None
        self.notes = {}