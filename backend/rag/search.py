import os
from langsmith import trace
from dotenv import load_dotenv
from langsmith import traceable
from .generator import generate
from .query_formatter import query_rewriter
from .retriever import embedding_search, bm25_search
from .utils import resolve_company, get_year_window, deduplicator, doc_to_text

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")

@traceable(name="pipeline_step")
def pipeline(query):

    with trace("get_year_window") as t:
        t.add_inputs({"query": query})
        years = get_year_window(query)
        t.add_outputs({"years": years})

    with trace("resolve_company") as t:
        t.add_inputs({"query": query})
        company = resolve_company(query)
        t.add_outputs({"company": company})

    rw_query = query_rewriter(query)
    
    bm25_docs = bm25_search(rw_query, company, years, 5)
    embed_docs = embedding_search(rw_query, company, years, 5)

    results = deduplicator(bm25_docs + embed_docs)
    source = doc_to_text(results)

    response = generate(query, source)
        
    selected_docs = [results[i] for i in response.indexes if i < len(results)]

    return {
        "answer": response.answer,
        "documents": [
            {"metadata": d.metadata, "page_content": d.page_content}
            for d in selected_docs
        ]
    }