import os
from typing import List
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",   
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )

def query_rewriter(query: str) -> List[str]:
    prompt = f"""
        You are an expert in financial language modeling and information retrieval. 
        Your task is to rewrite the given user query to maximize retrieval quality for both **embedding-based** and **BM25** search systems.
        
        Follow these instructions carefully:
        
        1. **Purpose:**  
           The rewritten query will be used to retrieve the most relevant passages from financial filings and reports.  
           It must retain the same intent but use more explicit, formal, and descriptive financial terminology.
        
        2. **Rewriting Guidelines:**  
           - Expand abbreviations and shorthand conservatively (e.g., "capex" → "capital expenditures" or "Property, Plant, and Equipment").  
           - Include relevant synonyms or equivalent financial terms that improve retrievability.  
           - Maintain professional, factual tone suitable for financial documents.  
           - Do **not** add speculative or interpretive phrasing — stay true to the question’s meaning.  
           - Keep the query concise, ideally 1–2 sentences.  
           - The rewritten version must be a **standalone, retrieval-friendly query**, not an explanation.
        
        3. **Output Format:**  
           Return only the rewritten query (no commentary or reasoning).
        
        ---
        
        Original Query:
        {query}
        
        Rewritten Query:
        """
    
    response = llm.invoke(prompt)
    return response.content
