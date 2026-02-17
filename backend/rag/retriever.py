import os
import zipfile
from langsmith import traceable
from dotenv import load_dotenv
from qdrant_client import models
from typing import List, Optional
from qdrant_client import QdrantClient
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse

load_dotenv()

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
QDRANT_DIR = os.path.join(BASE_DIR, "qdrant_db")
COLLECTION_NAME = "sec_filings"

def load_qdrant_vectorstore():

    if not os.path.exists(QDRANT_DIR):
        raise RuntimeError(f"Qdrant DB folder not found at {QDRANT_DIR}")

    dense_embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("FREE_GOOGLE_API_KEY"),
        task_type="RETRIEVAL_DOCUMENT",
        output_dimensionality=3072
    )

    sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")

    client = QdrantClient(path=QDRANT_DIR)

    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=dense_embeddings,
        sparse_embedding=sparse_embeddings,
        retrieval_mode=RetrievalMode.HYBRID,
        vector_name="dense",
        sparse_vector_name="sparse",
    )
    print("Qdrant DB running.")

    return vectorstore

vectorstore = load_qdrant_vectorstore()

@traceable(name="hybrid_retrieval", run_type = "retriever")
def retriever(queries: str, company: Optional[str] = None, year_window: List[int] = [], k: int = 10) -> List[Document]:

    must_conditions = []
    should_conditions = []

    if company:
        must_conditions.append(
            models.FieldCondition(
                key="metadata.company",
                match=models.MatchValue(value=company.lower())
            )
        )

    if year_window:
        for y in year_window:
            should_conditions.append(
                models.FieldCondition(
                    key="metadata.year",
                    match=models.MatchValue(value=y)
                )
            )

    filter_ = None
    if must_conditions or should_conditions:
        filter_ = models.Filter(
            must=must_conditions if must_conditions else None,
            should=should_conditions if should_conditions else None
        )

    docs = vectorstore.similarity_search(
        query=queries,
        k=k,
        filter=filter_
    )

    if not docs and company:
        docs = vectorstore.similarity_search(
            query=queries,
            k=k,
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.company",
                        match=models.MatchValue(value=company.lower())
                    )
                ]
            )
        )

    return docs