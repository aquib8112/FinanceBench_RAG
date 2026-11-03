import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from langsmith import traceable
from qdrant_client import QdrantClient, models

from .utils import LLMFailure

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1] / "data"
QDRANT_DIR = BASE_DIR / "qdrant_db"
COLLECTION_NAME = "sec_filings"


class GeminiQueryEmbeddings(GoogleGenerativeAIEmbeddings):
    # Embedding 2 uses a text instruction instead of the old task_type parameter.
    def embed_query(self, text: str) -> List[float]:
        result = self.client.models.embed_content(
            model=self.model,
            contents=f"task: search result | query: {text}",
            config={"output_dimensionality": self.output_dimensionality},
        )
        return list(result.embeddings[0].values)


def load_qdrant_vectorstore():
    if not (QDRANT_DIR / "meta.json").is_file():
        raise RuntimeError(f"Extract the Gemini Embedding 2 database into {QDRANT_DIR}")

    dense_embeddings = GeminiQueryEmbeddings(
        model="gemini-embedding-2",
        output_dimensionality=3072,
        vertexai=False,
    )  # Reads GOOGLE_API_KEY from the environment.
    sparse_embeddings = FastEmbedSparse(
        model_name="Qdrant/bm25",
        cache_dir=os.getenv("FASTEMBED_CACHE_PATH", str(BASE_DIR / "fastembed_cache")),
    )
    client = QdrantClient(path=str(QDRANT_DIR))
    try:
        params = client.get_collection(COLLECTION_NAME).config.params
        dense = params.vectors.get("dense")
        if (dense is None or dense.size != 3072 or dense.distance != models.Distance.COSINE
                or "sparse" not in (params.sparse_vectors or {})):
            raise ValueError("Expected the Gemini 2 index with dense (3072, cosine) and sparse vectors.")
        return QdrantVectorStore(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding=dense_embeddings,
            sparse_embedding=sparse_embeddings,
            retrieval_mode=RetrievalMode.HYBRID,
            vector_name="dense",
            sparse_vector_name="sparse",
            # Check the saved configuration above; avoid a dummy document API call.
            validate_collection_config=False,
        )
    except Exception:
        client.close()
        raise


vectorstore = load_qdrant_vectorstore()


def retriever(queries: str, company: Optional[str] = None,
              year_window: Optional[List[int]] = None, k: int = 8) -> List[Document]:
    company_filter = (
        [models.FieldCondition(key="metadata.company", match=models.MatchValue(value=company.lower()))]
        if company else []
    )
    year_filter = [
        models.FieldCondition(key="metadata.fiscal_year", match=models.MatchValue(value=year))
        for year in (year_window or [])
    ]
    filter_ = models.Filter(must=company_filter or None, should=year_filter or None) if company_filter or year_filter else None
    docs = vectorstore.similarity_search(query=queries, k=k, filter=filter_)

    # If the year window has no matches, retry within the same company.
    if not docs and company_filter and year_filter:
        docs = vectorstore.similarity_search(
            query=queries, k=k, filter=models.Filter(must=company_filter)
        )
    return docs


@traceable(name="hybrid_retrieval", run_type="retriever")
def retrieve_queries(queries: List[str], company: Optional[str] = None,
                     year_window: Optional[List[int]] = None, k: int = 8) -> List[Document]:
    # Trace all searches together and return one ordered, deduplicated page list.
    try:
        pages_by_id = {}
        for query in queries:
            for page in retriever(query, company, year_window, k=k):
                pages_by_id.setdefault(page.metadata["page_id"], page)
        return list(pages_by_id.values())
    except Exception as error:
        raise LLMFailure(f"Retrieval failed: {error}") from error
