import os
import shutil
from typing import Any, Callable
from langchain.schema.document import Document
from langchain_community.vectorstores import Chroma
from langchain.callbacks.base import BaseCallbackHandler
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.pdf import PyPDFDirectoryLoader
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, UnstructuredExcelLoader

# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

base_dir_files = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
base_dir_app = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def verify_directory_exists(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created.")
    else:
        print(f"Directory '{directory_path}' already exists.")

FILES_PATH = os.path.join(base_dir_files, 'files')
verify_directory_exists(FILES_PATH)
CHROMA_PATH = os.path.join(base_dir_app, 'database', 'chroma')
verify_directory_exists(CHROMA_PATH)

class StreamingCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.partial_output = ""

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        self.partial_output += token
        print(token, end="", flush=True)

def load_documents():
    files_and_folders = os.listdir(FILES_PATH)
    file_names = [f for f in files_and_folders if os.path.isfile(os.path.join(FILES_PATH, f))]

    ext = os.path.splitext(file_names[0])[-1].lower() # extensión del archivo en minúscula

    file_path = os.path.join(FILES_PATH, file_names[0])

    if ext == ".pdf":
        loader = PyPDFDirectoryLoader(os.path.dirname(FILES_PATH))
        print(f"📄 Downloading a PDF document.")
        documents = loader.load()
    elif ext == ".docx":
        loader = UnstructuredWordDocumentLoader(file_path)
        print(f"📝 Downloading a Word document.")
        documents = loader.load()
    elif ext == ".xlsx":
        loader = UnstructuredExcelLoader(file_path)
        print(f"📊 Downloading an Excel document.")
        documents = loader.load()
    else:
        raise ValueError(f"File format not supported: {ext}")

    return documents

def split_documents(documents: list[Document]):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )

    return splitter.split_documents(documents)

def get_embedding_function():
    embeddings = OllamaEmbeddings( # revisar acá si hacemos el request nosotros aparte porque hay un nuevo endpoint "http://localhost:11434/api/embed" que aún no se ha actualizado en langchaing-community
        model='nomic-embed-text',
        # base_url='http://ollama-container:11434'
    )
    return embeddings

def add_to_chroma(chunks: list[Document]):
    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=get_embedding_function()
    )

    # Calculate Page IDs.
    chunks_with_ids = calculate_chunk_ids(chunks)
    
    # Add or Update the documents.
    existing_items = db.get(include=[])  # IDs are always included by default
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Only add documents that don't exist in the DB.
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"👉 Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        print(f"Got new chunk IDs")
        db.add_documents(new_chunks, ids=new_chunk_ids)
        print("✅ New documents added")
    else:
        print("✅ No new documents to add")

def calculate_chunk_ids(chunks):

    # This will create IDs like "data/monopoly.pdf:6:2"
    # Page Source : Page Number : Chunk Index

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        # If the page ID is the same as the last one, increment the index.
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        # Calculate the chunk ID.
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Add it to the page meta-data.
        chunk.metadata["id"] = chunk_id

    return chunks

def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
