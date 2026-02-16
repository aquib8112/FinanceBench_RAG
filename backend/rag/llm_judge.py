import os
from typing import List
from google import genai
from .utils import LLMFailure
from dotenv import load_dotenv
from langsmith import traceable
from pydantic import BaseModel, Field

load_dotenv()

client = genai.Client(api_key=os.getenv("FREE_GOOGLE_API_KEY"))

def format_candidate(i, doc, max_chars=1500):
    meta = doc.metadata

    company = meta.get("company", "").upper()
    year = meta.get("year", "")
    doc_type = meta.get("document_type", "").upper()

    content = doc.page_content[:max_chars]

    return f"""[ID: {i}]
            Company: {company}
            Year: {year}
            Document: {doc_type}
            
            Content:
            {content}
            """

class JudgeResults(BaseModel):
    ids: List[int] = Field(
        description=(
            "List of numeric passage IDs to keep. "
            "Each ID must correspond to a candidate passage index. "
            "Return an empty list if no passages are relevant."
        )
    )

@traceable(name="llm_judge", run_type = "llm")
def llm_judge(query, docs):
    candidates_text = "\n\n".join(
        format_candidate(i, docs[i]) for i in range(len(docs))
    )

    prompt = f"""
                You are a financial research assistant.
                
                Task:
                Given a user query and candidate passages from SEC filings,
                identify all passages that are NOT clearly irrelevant to answering the query.
                
                Inclusion rules:
                - Include passages containing facts, figures, definitions, tables, footnotes,
                  contextual explanations, or background information related to the query.
                - A passage does NOT need to directly answer the query.
                - If a passage might contribute evidence used by an expert, INCLUDE it.
                - Prefer false positives over false negatives.
                
                Exclusion rules:
                - Exclude a passage ONLY if it is clearly about:
                  - a different company,
                  - a different reporting period,
                  - or a completely unrelated financial topic.
                
                Hard constraints:
                - Select passages ONLY by their numeric IDs.
                - IDs are zero-based and must be within the provided list.
                - Do NOT return passage text or explanations.
                - If 5 or more candidates are provided, return AT LEAST 5 IDs unless none are relevant.
                
                Output format:
                Return a JSON object exactly matching:
                {{ "ids": [0, 2, 5] }}
                
                If none are relevant, return:
                {{ "ids": [] }}
                
                User query:
                {query}
                
                Candidate passages:
                {candidates_text}
                """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config={
                "temperature": 0.0,
                "top_p": 0.1,
                "seed": 42,
                "response_mime_type": "application/json",
                "response_json_schema": JudgeResults.model_json_schema(),
            },
        )


        result = JudgeResults.model_validate_json(response.text)
        return [docs[i] for i in result.ids if 0 <= i < len(docs)]
    
    except Exception as e:
        raise LLMFailure(f"Generation failed: {e}")