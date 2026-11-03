import re

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.utils.function_calling import convert_to_json_schema
from langchain_openrouter import ChatOpenRouter as BaseChatOpenRouter
from rapidfuzz import fuzz, process

class ChatOpenRouter(BaseChatOpenRouter):
    """Report OpenRouter's actual charge to LangSmith for non-streaming calls."""

    def _create_chat_result(self, response):
        result = super()._create_chat_result(response)
        for generation in result.generations:
            message = generation.message
            cost = message.response_metadata.get("cost")
            if cost is not None and message.usage_metadata is not None:
                message.usage_metadata["total_cost"] = cost
        return result


class LLMFailure(Exception):
    """Raised when an LLM call fails in a recoverable way."""
    pass

def bind_json_schema(model, schema):
    json_schema = convert_to_json_schema(schema)
    return model.bind(
        response_format={
            "type": "json_schema",
            "json_schema": {"name": json_schema.get("title", ""), "schema": json_schema, "strict": True},
        },
        ls_structured_output_format={
            "kwargs": {"method": "json_schema", "strict": True}, "schema": json_schema,
        },
    )


def invoke_json_schema(model, prompt, schema):
    # Keep the model and existing Pydantic parser traced without a sequence wrapper.
    message = model.invoke(prompt)
    return PydanticOutputParser(pydantic_object=schema).invoke(message)


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
