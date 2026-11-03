from dotenv import load_dotenv
from langsmith import trace, traceable

from .generator import generator
from .llm_judge import context_judge
from .query_formatter import query_decomposer
from .retriever import retrieve_queries
from .utils import LLMFailure, get_year_window, resolve_company

load_dotenv()


@traceable(name="pipeline_step")
def pipeline(query):
    try:
        with trace("get_year_window", run_type="tool") as run:
            run.add_inputs({"question": query})
            years = get_year_window(query)
            run.add_outputs({"years": years})
        with trace("resolve_company", run_type="tool") as run:
            run.add_inputs({"question": query})
            company = resolve_company(query)
            run.add_outputs({"company": company})

        plan = query_decomposer(query)
        pages = retrieve_queries(plan.queries, company, years, k=8)

        judgment = context_judge(query, plan.queries, pages)
        useful_pages = [pages[audit.page_index] for audit in judgment.pages if audit.is_useful]
        # Useful pages still reach generation when context is insufficient; no search retry.
        response = generator(query, useful_pages)
        selected_docs = [useful_pages[index] for index in response.indexes]

        return {
            "answer": f"## Reasoning\n{response.reasoning}\n\n## Answer\n{response.answer}",
            "documents": [
                {"metadata": page.metadata, "page_content": page.page_content}
                for page in selected_docs
            ],
        }

    except LLMFailure as error:
        error_str = str(error).upper()
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            user_message = "The model provider's request limit was reached. Please try again later."
        elif any(code in error_str for code in ["503", "529", "SERVICE_UNAVAILABLE", "DEADLINE_EXCEEDED"]):
            user_message = "The model provider is temporarily unavailable. Please try again shortly."
        else:
            user_message = "An unexpected error occurred while answering your question. Please try again."
        return {"answer": user_message, "documents": [], "error": str(error)}
