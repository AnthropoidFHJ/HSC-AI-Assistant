from src.chunker import load_pdf_file, text_split, download_hugging_face_embeddings
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os

load_dotenv()

PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

pc = Pinecone(api_key=PINECONE_API_KEY)

index_name = "hsc-ai-assistant"
existing_indexes = [index.name for index in pc.list_indexes()]

if index_name not in existing_indexes:

    print(f"Creating new index: {index_name}")
    extracted_data = load_pdf_file(data='data/')
    text_chunks = text_split(extracted_data)
    embeddings = download_hugging_face_embeddings()
    
    pc.create_index(
        name=index_name,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1",
        )
    )

    import time
    time.sleep(1)
    
    docsearch = PineconeVectorStore.from_documents(
        documents=text_chunks,
        index_name=index_name,
        embedding=embeddings
    )
    print("Documents indexed successfully.")
else:
    print(f"Using existing index: {index_name}")
    embeddings = download_hugging_face_embeddings()
    docsearch = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )