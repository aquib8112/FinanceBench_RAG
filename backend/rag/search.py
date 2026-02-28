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
        error_str = str(e).upper()
    
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            user_message = "The system has reached the maximum daily request limit for the free service tier. Access will be restored once the quota resets."
        
        elif any(code in error_str for code in ["503", "529", "SERVICE_UNAVAILABLE", "DEADLINE_EXCEEDED"]):
            user_message = "The underlying model provider is currently experiencing high traffic volumes. Please attempt your request again in a few moments."
            
        else:
            user_message = "An unexpected error occurred during response generation. Please verify your query and try again."
        return {
            "answer": user_message,
            "documents": [],
            "error": str(e)
        }