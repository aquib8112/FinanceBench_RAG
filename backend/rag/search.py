from dotenv import load_dotenv
from langsmith import trace, traceable

from .generator import generator
from .llm_judge import context_judge
from .query_formatter import query_decomposer
from .retriever import retrieve_queries
from .utils import LLMFailure, get_year_window, resolve_company

load_dotenv()


@traceable(name="pipeline_step")
def pipeline(query, on_progress=None):
    notify = on_progress or (lambda _: None)
    try:
        with trace("get_year_window", run_type="tool") as run:
            run.add_inputs({"question": query})
            years = get_year_window(query)
            run.add_outputs({"years": years})
        with trace("resolve_company", run_type="tool") as run:
            run.add_inputs({"question": query})
            company = resolve_company(query)
            run.add_outputs({"company": company})

        notify({"message": "Planning the search\u2026", "company": company, "years": years})
        plan = query_decomposer(query)
        notify({"message": "Searching the filings\u2026", "company": company, "query_count": len(plan.queries)})
        pages = retrieve_queries(plan.queries, company, years, k=8)

        notify({
            "message": f"Reviewing {len(pages)} candidate page{'s' if len(pages) != 1 else ''}\u2026",
            "detail": "Checking which pages address your question.",
        })
        judgment = context_judge(query, plan.queries, pages)
        useful_audits = [audit for audit in judgment.pages if audit.is_useful]
        useful_pages = [pages[audit.page_index] for audit in useful_audits]
        # Useful pages still reach generation when context is insufficient; no search retry.
        notify({"message": "Writing your answer\u2026", "selected_count": len(useful_pages)})
        response = generator(query, useful_pages)
        selected_docs = [useful_pages[index] for index in response.indexes]
        cited_indexes = {useful_audits[index].page_index for index in response.indexes}
        research = {
            "company": company,
            "years": years,
            "queries": plan.queries,
            "required_data_points": judgment.required_data_points,
            "retrieved_count": len(pages),
            "selected_count": len(useful_pages),
            "cited_count": len(selected_docs),
            "is_context_enough": judgment.is_context_enough,
            "sufficiency_reason": judgment.sufficiency_reason,
            "missing_information": judgment.missing_information,
            "pages": [
                {
                    "metadata": {
                        key: value for key, value in pages[audit.page_index].metadata.items()
                        if key in {"company", "fiscal_year", "year", "fiscal_quarter", "quarter",
                                   "document_type", "page_in_pdf", "fiscal_date"}
                    },
                    "analysis": audit.analysis,
                    "is_cited": audit.page_index in cited_indexes,
                }
                for audit in useful_audits
            ],
        }

        return {
            "answer": f"## Reasoning\n{response.reasoning}\n\n## Answer\n{response.answer}",
            "research": research,
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
