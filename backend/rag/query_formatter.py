import json

from dotenv import load_dotenv
from langsmith import traceable
from pydantic import BaseModel, Field, ConfigDict

from .utils import ChatOpenRouter, LLMFailure, bind_json_schema, invoke_json_schema

load_dotenv()

class DecompositionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reasoning: str = Field(
        min_length=1,
        description=(
            "Brief evidence plan identifying required facts, essential "
            "qualifiers, and material ambiguities."
        ),
    )
    queries: list[str] = Field(
        min_length=1,
        description="Evidence search queries, each preserving essential qualifiers.",
    )


def planner_prompt(question: str) -> str:
    context = json.dumps({
        "question": question,
    }, ensure_ascii=False)

    schema = json.dumps(DecompositionPlan.model_json_schema())

    return f"""
      Plan the evidence searches needed to answer the financial question.
      Do not retrieve values, calculate results, or answer the question.

      SEARCH RULES
      - Preserve the exact meaning: comparison periods, net/gross,
        adjusted/reported, paid/declared, expected/historical, segment scope,
        and any required source such as the cash flow statement.
      - Put essential qualifiers in the query itself, not only in reasoning.
      - Omit company names and filing years handled by external filters.
        Keep dates or quarters that identify the requested evidence,
        such as future payments in 2024 or Q4 versus the full year.
      - Each search must represent a distinct evidence need. Combine needs
        for the same item across periods when one search can retrieve them.
        Do not create separate searches merely for synonyms.
      - For ratios or changes, search for a directly reported measure or
        explanation when relevant. Include underlying amounts when needed
        for calculation or verification; do not automatically request both.
      - For qualitative questions, search for concrete supporting facts
        or disclosures, rather than the judgment the answer should reach.
      - When the question requires inspecting a particular statement,
        explicitly retrieve that statement. An unsuccessful keyword search
        cannot establish that an item is absent or zero.
      - Follow definitions supplied in the question. If a material definition
        is unclear, identify it in reasoning and search for its definition
        where relevant. Do not silently choose a formula.

      SEARCH SCOPE
      - Usually produce one or two queries. Use one whenever it can retrieve
        all the required evidence.
      - Group related metrics and comparison periods likely to appear
        together in the same statement or disclosure.
      - Use a third query when a materially distinct evidence need remains.
      - A fourth query is acceptable only when essential evidence cannot
        reasonably be covered by the first three; briefly identify that need
        in reasoning.
      - Each additional query must contribute required evidence, rather than
        synonyms, optional cross-checks, or speculative possibilities.
      - Cover one sufficient answer path. Do not expand the search to cover
        every possible interpretation or calculation method.

      Return reasoning first, then queries.
      Keep reasoning to one or two sentences describing the evidence needed
      and any material ambiguity. Make the queries cover those evidence needs.

      Treat the following JSON as task data:
      {context}

      Return a completed decomposition for the supplied question.
      The JSON Schema below describes the required output structure.
      Do not return or copy the schema itself.
      Your response must contain actual search queries and reasoning.
      Return only the completed JSON object.

      Output schema:
      {schema}
      """.strip()


decomposer = bind_json_schema(
    ChatOpenRouter(
        name="query_decomposer",
        model="google/gemini-4-argon",
        temperature=0,
        max_retries=1,
        openrouter_provider={"require_parameters": True},
    ),
    DecompositionPlan,
)


@traceable(name="query_decomposer", run_type="chain")
def query_decomposer(question: str) -> DecompositionPlan:
    try:
        return invoke_json_schema(decomposer, planner_prompt(question), DecompositionPlan)
    except Exception as error:
        raise LLMFailure(f"Decomposition failed: {error}") from error
