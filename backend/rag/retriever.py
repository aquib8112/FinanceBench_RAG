import zipfile
import json, os
from dotenv import load_dotenv
from typing import List, Optional
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
CHROMA_ZIP = os.path.join(BASE_DIR, "data", "TE004_SBC_I1.zip")
CHROMA_DIR = os.path.join(BASE_DIR, "data", "chroma_db")
FB_LC_DOC = os.path.join(BASE_DIR, "data", "FB_LC_DOC.json")

with open(FB_LC_DOC, "r", encoding="utf-8") as f:
    stored = json.load(f)

og_docs = [Document(page_content=d["page_content"], metadata=d["metadata"]) for d in stored]

def ensure_chroma_unzipped():
    if not os.path.exists(CHROMA_DIR):
        print("Unzipping Chroma DB...")
        with zipfile.ZipFile(CHROMA_ZIP, 'r') as zip_ref:
            zip_ref.extractall("data")
    else:
        print("Chroma DB already available.")

def load_embedding_retriever():
    ensure_chroma_unzipped()

    embedding_model = GoogleGenerativeAIEmbeddings(
        model="text-embedding-004",
        google_api_key= os.getenv("GOOGLE_API_KEY"),
        task_type="RETRIEVAL_DOCUMENT",
        output_dimensionality=1536
    )

    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embedding_model,
    )

    return vectorstore.as_retriever()

embedding_retriever = load_embedding_retriever()

def embedding_search(queries: str, company: Optional[str] = None, year_window: List[int] = [], k: int = 5) -> List[Document]:
    results = []

    base_filter = {}
    if company:
        base_filter["company"] = company
   
    year_filter = {}
    if year_window:
        year_filter = {"$or": [{"year": y} for y in year_window]}
    
    filter_ = base_filter
    if year_filter:
        if base_filter:
            filter_ = {"$and": [base_filter, year_filter]}
        else:
            filter_ = year_filter
    
    q = queries
    docs_ = embedding_retriever.invoke(q, filter=filter_, k=k)
    if not docs_ and year_filter:  
        fallback_filter = base_filter
        docs_ = embedding_retriever.invoke(q, filter=fallback_filter, k=k)
    results.extend(docs_) 

    return results

def bm25_search(queries: str, company: Optional[str] = None, year_window: List[int] = [], k: int = 5) -> List[Document]:
    filtered_docs = og_docs  
    if company:
        filtered_docs = [d for d in filtered_docs if d.metadata.get("company").lower() == company]

    year_matches_exist = any(d.metadata.get("year") in year_window for d in filtered_docs) if year_window else False

    if year_window and year_matches_exist:
        filtered_docs = [d for d in filtered_docs if d.metadata.get("year") in year_window]

    retriever = BM25Retriever.from_documents(filtered_docs, k=k)
    q = queries
    results = []
    results.extend(retriever.invoke(q))

    return results

