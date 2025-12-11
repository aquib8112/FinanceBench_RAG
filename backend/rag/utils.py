import re
from typing import List
from rapidfuzz import fuzz, process
from langchain_core.documents import Document

def resolve_company(query: str, threshold: int = 80) -> str | None:
    COMPANY_ALIASES = {
    "3m": ["3m"],
    "activisionblizzard": ["activision blizzard", "activision", "blizzard"],
    "adobe": ["adobe"],
    "aes": ["aes", "applied energy services"],
    "amazon": ["amazon"],
    "amcor": ["amcor"],
    "amd": ["amd", "advanced micro devices"],
    "americanexpress": ["american express", "amex"],
    "americanwaterworks": ["american water works"],
    "bestbuy": ["best buy"],
    "block": ["block", "square"],
    "boeing": ["boeing"],
    "cocacola": ["coca cola", "coke"],
    "corning": ["corning"],
    "costco": ["costco"],
    "cvshealth": ["cvs", "cvs health"],
    "footlocker": ["foot locker", "footlocker"],
    "generalmills": ["general mills"],
    "johnson_johnson": ["johnson & johnson", "jnj", "johnson johnson"],
    "jpmorgan": ["jpmorgan", "jp morgan","jpmorgan chase", "jpm"],
    "kraftheinz": ["kraft heinz", "kraft", "heinz"],
    "lockheedmartin": ["lockheed martin"],
    "mgmresorts": ["mgm resorts", "mgm"],
    "microsoft": ["microsoft"],
    "netflix": ["netflix"],
    "nike": ["nike"],
    "paypal": ["paypal"],
    "pepsico": ["pepsico", "pepsi"],
    "pfizer" : ["pfizer"],
    "ultabeauty": ["ulta beauty", "ulta"],
    "verizon": ["verizon"],
    "walmart": ["walmart"]
    }

    CANONICAL_NAMES = list(COMPANY_ALIASES.keys())
    q = query.lower()

    for canon, aliases in COMPANY_ALIASES.items():
        for alias in aliases:
            if alias in q:
                return canon

    match, score, _ = process.extractOne(q, CANONICAL_NAMES, scorer=fuzz.partial_ratio)
    if score >= threshold:
        return match

    return None

def get_year_window(question: str):

    patterns = [
        r'\bFY\s*(\d{2,4})[A-Z]?Q?\d?\b',  # FY22, FY2023, FY2023Q1, FY 2021
        r'\bQ\d{1,2}(\d{4})\b',          # Q12023, Q2 2023
        r'\b(\d{4})\b'                   # Standalone 2023
    ]
    
    years = set()
    question_upper = question.upper()
    
    for pattern in patterns:
        matches = re.findall(pattern, question_upper)
        for match in matches:
            try:
                year = int(match)
                if len(match) == 2: 
                    year += 2000
                if 2015 <= year <= 2024:
                    years.add(year)
            except ValueError:
                continue  
    
    if not years:
        return []
    
    min_year = min(years)
    max_year = max(years)
    
    start = max(2015, min_year - 1)
    end = min(2024, max_year + 1)
    
    return sorted(list(range(start, end + 1)))

def deduplicator(docs: List[Document]) -> List[Document]:
    seen_ids = set()
    unique_docs = []

    for doc in docs:
        chunk_id = doc.metadata["uid"]
        if chunk_id not in seen_ids:
            seen_ids.add(chunk_id)
            unique_docs.append(doc)

    return unique_docs

def doc_to_text(docs):
    chunks = []
    for i, doc in enumerate(docs):
        m = doc.metadata
        chunk = (
            f"=== DOCUMENT {i} ===\n"
            f"document name: {m.get('document_name')}\n"
            f"page number: {m.get('page_in_pdf')}\n"
            f"CONTENT:\n{m.get('full_text')}\n"
            f"=== END DOCUMENT {i} ===\n"
        )
        chunks.append(chunk)

    return "\n".join(chunks)