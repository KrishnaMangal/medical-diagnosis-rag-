import os
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from ..config.db import report_collection
from typing import List
from fastapi import UploadFile

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "rbac-diagnosis-index")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploaded_reports")

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY # Set the environment variable for Google API key

os.makedirs(UPLOAD_DIR, exist_ok=True) # Ensure upload directory exists


# Initialize Pinecone client and index
pc=Pinecone(api_key=PINECONE_API_KEY)
spec = ServerlessSpec(
    cloud="aws",
    region=PINECONE_ENV
)

existing_indexes = [i["name"] for i in pc.list_indexes()]

if PINECONE_INDEX_NAME not in existing_indexes:
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=3072,
        metric="dotproduct",
        spec=spec
    )
    while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
        time.sleep(1)

index = pc.Index(PINECONE_INDEX_NAME)  # using index for upsert and query operations

async def load_vectorstore(uploaded_files: List[UploadFile], uploader: str, doc_id: str):
    embed_model = GoogleGenerativeAIEmbeddings(model="embedding-001")
    for file in uploaded_files:
        filename = Path(file.filename).name
        save_path = Path(UPLOAD_DIR) / f"{doc_id}_{filename}"
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)
        
        # load the pdf page
        loader = PyPDFLoader(str(save_path))
        documents = loader.load()
        
        # split the document into chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        chunks = splitter.split_documents(documents)
        
        # metadata generation
        texts = [chunk.page_content for chunk in chunks]
        ids = [f"{doc_id}-{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source": filename,
                "doc_id": doc_id,
                "uploader": uploader,
                "page": chunk.metadata.get("page", None),
                "text": chunk.page_content[:2000]
            }
            for chunk in chunks
        ]
        
        # get embedding in a thread
        # embed_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004",google_api_key=GOOGLE_API_KEY)
        
        # 2. Embeddings generate karein
        # embeddings = await asyncio.to_thread(
        #     embed_model.embed_documents,
        #     texts)
        
        # upsert to pinecone in a thread
        # async def upsert():
        #     index.upsert(
        #         vectors=list(zip(ids, embeddings, metadatas))
        #     )
        # await asyncio.to_thread(upsert)
        # --- UPDATED EMBEDDING SECTION ---
        # direct access to embeddings with correct model name
        embed_model = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
        
        try:
            print("Generating embeddings...")
            embeddings = await asyncio.to_thread(
                embed_model.embed_documents,
                texts
            )
            print("Embeddings generated!")
        except Exception as e:
            print(f"Embedding failed: {e}")
            raise e

        # --- UPDATED PINECONE UPSERT SECTION ---
        # Simplest way to upsert in a thread
        def do_upsert():
            vectors = list(zip(ids, embeddings, metadatas))
            index.upsert(vectors=vectors)

        await asyncio.to_thread(do_upsert)
        print("Upsert to Pinecone successful!")
        # store metadata in mongodb

        report_collection.insert_one({
            "doc_id": doc_id,
            "filename": filename,
            "uploader": uploader,
            "num_chunks": len(chunks),
            "uploaded_at": time.time()
        })



