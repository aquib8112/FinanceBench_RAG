import os
from langsmith import trace
from dotenv import load_dotenv
from langsmith import traceable
from .generator import generate
from .llm_judge import llm_judge
from .retriever import retriever
from .query_formatter import query_rewriter
from .utils import LLMFailure, resolve_company, get_year_window, doc_to_text

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")

@traceable(name="pipeline_step")
def pipeline(query):
    try:
        with trace("get_year_window", run_type="tool") as t:
            years = get_year_window(query)

        with trace("resolve_company", run_type="tool") as t:
            company = resolve_company(query)

        rw_query = query_rewriter(query)

        results = retriever(rw_query, company, years, k=10)
        results = llm_judge(query, results)

        source = doc_to_text(results)
        response = generate(query, source)

        selected_docs = [
            results[i] for i in response.indexes if i < len(results)
        ]

        return {
            "answer": response.answer,
            "documents": [
                {"metadata": d.metadata, "page_content": d.page_content}
                for d in selected_docs
            ]
        }

    except LLMFailure as e:
        # controlled failure
        return {
            "answer": "The system could not generate a reliable answer.",
            "documents": [],
            "error": str(e)
        }