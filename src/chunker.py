from langchain_community.document_loaders import PDFPlumberLoader, DirectoryLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.replace(' ।', '।').replace('। ', '। ')
    text = re.sub(r'\bPage\s*\d+\b', '', text, flags=re.IGNORECASE)
    return text.strip()

def load_pdf_file(data):
    loader = DirectoryLoader(
        data,
        glob="*.pdf",
        loader_cls=PDFPlumberLoader
    )
    docs = loader.load()
    for doc in docs:
        if hasattr(doc, 'page_content'):
            doc.page_content = clean_text(doc.page_content)
    return docs

def text_split(extracted_data):
    sentence_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", "।।", "।", "?", "!"],
        length_function=len,
        is_separator_regex=False
    )

    text_chunks = []

    for doc in extracted_data:
        if isinstance(doc, str):
            doc = Document(page_content=doc)

        chunks = sentence_splitter.split_documents([doc])
        text_chunks.extend(chunks)

    logger.info(f"Generated {len(text_chunks)} chunks")
    return text_chunks

def download_hugging_face_embeddings():
    embeddings = HuggingFaceEmbeddings(
        model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
        model_kwargs={'device': 'cpu'}
        )
    logger.info("Successfully loaded embeddings model.")
    return embeddings