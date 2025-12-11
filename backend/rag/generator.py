import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser

load_dotenv()

llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",   
        google_api_key = os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )

class FinanceAnswerSchema(BaseModel):
    answer: str = Field(
        description="Final analytical answer in Markdown format, with '## Reasoning' and '## Conclusion' sections."
    )
    indexes: List[int] = Field(
        description="List of document indexes (0-based) that were used to produce the answer.",
        default_factory=list
    )

parser = PydanticOutputParser(pydantic_object=FinanceAnswerSchema)


prompt = ChatPromptTemplate.from_template("""
    You are an expert financial analyst. Your task is to reason carefully before answering.

    Follow these steps **strictly**:
    1. **Analyze the question** — clarify what is being asked (ratios, trends, liquidity, risks, etc.).
    2. **Extract relevant data or facts** only from the provided source.
    3. **Connect those facts** using logical financial reasoning to form a conclusion.
    4. **Present your final answer** clearly and concisely, focusing on accuracy and analytical depth.

    Guidelines:
    - Use only the information given in the source.
    - Do not guess or rely on outside knowledge.
    - If the answer cannot be found, write exactly: **"Not found in source."**
    - Use a professional tone and avoid redundancy.
    - **Format your answer using clean Markdown with two sections:**
        - `## Reasoning`
        - `## Conclusion`

    Additional requirements:
    - Return your Markdown content inside the `"answer"` field.
    - `"indexes"` must list the 0-based indexes of the documents used.
    - If your conclusion is not found in source, then:
        - The `indexes` list MUST be empty (`[]`).
    - The final output must be valid JSON matching this Pydantic schema:
    {format_instructions}

    ---

    Question:
    {question}

    Source:
    {source}

    ---

    Answer:
    """)

def generate(question: str, source_text: str):

    formatted_prompt = prompt.format(
        question=question,
        source=source_text,
        format_instructions=parser.get_format_instructions()
    )

    raw = llm.invoke(formatted_prompt)
    return parser.parse(raw.content)    