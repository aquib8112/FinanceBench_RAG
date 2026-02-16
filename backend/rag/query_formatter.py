import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from .utils import LLMFailure
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser

load_dotenv()

llm = ChatGoogleGenerativeAI(
   model="gemini-2.5-flash-lite",
   google_api_key=os.getenv("FREE_GOOGLE_API_KEY"),
   temperature=0,
   top_p=0.1,
   seed=42
)

class RetrievalQuerySchema(BaseModel):
    rewritten_query: str = Field(
        description=(
            "A concise, retrieval-optimized query written in formal financial language,"
            "containing only the factual information need suitable for searching "
            "SEC filings (10-K, 10-Q, 8-K) and earnings call transcripts. "
            "All reasoning, evaluation, or explanatory clauses must be removed."
        )
    )

parser = PydanticOutputParser(pydantic_object=RetrievalQuerySchema)

QUERY_REWRITE_PROMPT = ChatPromptTemplate.from_template("""
        You are an expert system for financial document retrieval over SEC filings and earnings materials.

        Your task is to rewrite the user input into a single declarative retrieval query that will be used only for embedding-based and BM25 search over:
        Form 10-K
        Form 10-Q
        Form 8-K
        Earnings call transcripts
        Page-level financial summaries derived from these documents
        
        The rewritten query must strictly follow these rules:
        
        1. Declarative form only
        - The output must be a declarative noun phrase or statement.
        - Do NOT phrase the output as a question.
        - Do NOT include interrogatives such as “what,” “whether,” or “does.”
        
        2. Reported facts only
        - Include only financial information that is explicitly reported in filings.
        - Refer only to concrete line items, disclosures, or reported figures.
        - Do NOT include opinions, judgments, interpretations, or evaluations.
        
        3. No trends, assessments, or health judgments
        - Remove all language related to:
            - trends
            - improvement or deterioration
            - stability or health
            - performance evaluation
        - If the original query implies analysis, reduce it to the underlying reported facts required to perform that analysis.
        
        4. Decompose derived metrics
        - Do NOT include ratios, margins, conversions, or derived metrics directly.
        - Rewrite such requests using their underlying reported components.
            - Example: operating margin → operating income and revenue
            - Example: free cash flow → cash from operations and capital expenditures
        
        5. Filing-aligned terminology
        - Use terminology consistent with reported financial statement line items.
        - Prefer standard GAAP naming conventions where applicable.
        - Mention financial statements by name (e.g., “Consolidated Balance Sheet,” “Consolidated Statement of Cash Flows”).
        - Do NOT reference specific subsections or internal headings.
        
        6. Single fiscal period
        - Each rewritten query must refer to exactly one fiscal year or one fiscal quarter.
        - Do NOT combine multiple periods in a single query.
        
        7. No filler or meta language
        - Do NOT use verbs such as:
            - analyze
            - assess
            - determine
            - evaluate
            - identify 
        - Do NOT reference the user, the question, or the act of answering.
        - Do NOT explain or justify the rewrite.
        
        8. Single output  
        - Produce exactly one rewritten query.
        - Do NOT return multiple variants.
        - Do NOT include explanations or commentary.

        Important:
        - Output must be valid JSON only.
        - Do NOT use Markdown.
        - Do NOT wrap the output in code fences.
        - Do NOT include any text outside the JSON object.
        
        ----- 
        
        Output format:
        {format_instructions}
        
        User Input:
        {query}
        
        Rewritten Retrieval Query:
        """)

def query_rewriter(query: str) -> str:
    try :
        formatted_prompt = QUERY_REWRITE_PROMPT.format(
            query=query,
            format_instructions=parser.get_format_instructions()
        )

        response = llm.invoke(formatted_prompt)

        parsed = parser.parse(response.content)
        return parsed.rewritten_query
    
    except Exception as e:
        raise LLMFailure(f"Query rewrite failed: {e}")
