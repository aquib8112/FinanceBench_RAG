import os
from typing import List
from google import genai
from .utils import LLMFailure
from dotenv import load_dotenv
from langsmith import traceable
from pydantic import BaseModel, Field

load_dotenv()

client = genai.Client(api_key=os.getenv("FREE_GOOGLE_API_KEY"))
class FinanceAnswerSchema(BaseModel):
    answer: str = Field(
        description="Final analytical answer in Markdown format, with '## Reasoning' and '## Conclusion' sections."
    )
    indexes: List[int] = Field(
        description="List of document indexes (0-based) that were used to produce the answer.",
        default_factory=list
    )

@traceable(name="generator", run_type = "llm")
def generate(question: str, source_text: str):

    prompt = f"""
        You are an expert financial analyst. Your task is to reason carefully before answering.
        
        Follow these steps **strictly**:
        1. **Analyze the question** — determine what is being asked (ratios, trends, liquidity, risks, etc.). 
        2. **Identify relevant documents** — from the provided sources, select only documents that contain facts or data directly related to the question. Ignore any unrelated passages completely. 
        3. **Extract relevant data or facts** — only from documents identified as relevant. 
        4. **Connect those facts** using logical financial reasoning to form a conclusion. 
        5. **Present your final answer** clearly and concisely, focusing on accuracy and analytical depth.
        
        Guidelines:
        - Use only information from the relevant documents.
        - Do not guess or rely on outside knowledge.
        - If the answer cannot be found in the relevant documents, write exactly: **"Not found in source."**
        - Use a professional tone and avoid redundancy.
        - **Format your answer using clean Markdown with two sections:**
            - `## Reasoning`
            - `## Conclusion`
        
        Additional requirements:
        - Return your Markdown content inside the `"answer"` field.
        - `"indexes"` must list the 0-based indexes of documents actually used.
        - You may only list a document index if you directly quoted or paraphrased content from that document.
        - If no relevant documents exist, `"indexes"` must be empty (`[]`) and `"answer"` should be "Not found in source."
        
        ---
        
        Question:
        {question}
        
        Source:
        {source_text}
        
        ---
        
        Answer:

        """

    try :
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config={
                "temperature": 0.0,
                "top_p": 0.1,
                "seed": 42,
                "response_mime_type": "application/json",
                "response_json_schema": FinanceAnswerSchema.model_json_schema(),
            },
        )

        result = FinanceAnswerSchema.model_validate_json(response.text)
        return result
    
    except Exception as e:
        raise LLMFailure(f"Judge failed: {e}")