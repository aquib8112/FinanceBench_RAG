import json
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


CHUNKS_FILE = Path("")  # insert chunks file path


class PageInventory(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    summary: Annotated[str, Field(min_length=1)] = Field(
        description=(
            "A compact page content inventory for retrieval: substantive table "
            "and disclosure names, distinctive product/transaction/program names, "
            "grouped useful metric/category labels with their own scope and source "
            "periods. Brief identity and purpose for cover/index pages. "
            "Name narrative subjects and driver categories "
            "without explaining outcomes, trends, causes or footnote rules. "
            "No financial values, conclusions or repeated topic descriptions."
        )
    )


summary_schema = PageInventory.model_json_schema()

def summary_prompt(chunk):
    context = json.dumps(
        {
            "document_name": chunk["document_name"],
            "company": chunk["company"],
            "fiscal_date": chunk["fiscal_date"],
            "page_id": chunk["page_id"],
            "xml_text": chunk["xml_text"],
        },
        ensure_ascii=False,
    )
    return f"""
    <task>
    Write a compact content inventory of this financial-report page for search.
    The search result returns the FULL ORIGINAL PAGE for answering questions.
    Identify available evidence, without summarizing findings. Use only PAGE DATA.
    Return JSON with one "summary" string.
    </task>

    <rules>
    - Write short topic phrases separated by semicolons. Name substantive tables,
      useful metric/category labels and independent narrative disclosures. Avoid
      introductions, repeated labels and a separate item for each year or cell.
    - Describe each table or section from its own local heading and labels:
      topic, supported scope, metrics and their respective periods. Combine clauses
      only when these associations stay clear. Group metrics under shared dates
      only when ALL grouped metrics cover those dates. Different date coverage
      needs separate metric-period phrases, even within one table.
    - A company/segment/geographic heading scopes the following section until a
      new heading at the same or higher level changes it. A date-only or period-only
      subheading changes the period, not the reporting entity. Do not reset a
      segment to the whole company because a paragraph has no segment name.
      A later heading cannot scope earlier continuation text. Omit unresolved
      scope rather than guessing from document metadata.
    - Use periods printed on the page, even when they differ from the filename.
      Preserve consolidated/segment, reported/adjusted, net/gross, actual/forecast
      and quarter/year-to-date distinctions. Repeated versions of the same table
      may share one label list, with each actual/forecast time horizon explicit.
    - Retain useful categories such as inventory, receivables, property, plant
      and equipment, leases, debt, pensions and equity when present. Group cash
      flows by operating/investing/financing activities, retaining distinctive
      subjects such as capital spending, acquisitions, borrowings and buybacks.
      Skip routine totals/subtotals, beginning/ending balances and reconciliation
      mechanics unless they are the specific subject. Do not enumerate every row.
    - Preserve distinctive product/drug, transaction, counterparty, segment,
      program and study names. List announcement subjects under their categories;
      generic "regulatory announcements" cannot replace named products.
      Keep source terminology and a useful alias once. Omit promotional wording.
    - For narrative, name subjects and driver categories, such as "sales drivers:
      pricing, volumes and currency" or "debt covenants and dividend restrictions".
      Name definitions, reconciliations, exclusions and absence disclosures as
      topics. Do not explain trends, causes, footnote rules, restriction outcomes
      or management expectations. Do not calculate or invent findings.
    - Omit monetary/operating quantities, percentages, ratio values, quantified
      guidance, rating codes and par values, including values written in words.
      Amounts embedded in a program/facility/transaction label are values too:
      identify it by subject, source name and useful announcement/maturity dates,
      not its size or ownership percentage. Keep metric names, years, dates,
      period lengths and useful note/standard/form identifiers. No placeholders.
    - Keep each topic once. Remove repetition before dropping independent topics
      or distinctive names; no word quota. Do not invent titles, repair damaged
      source text, or add evidence from other pages.
    - Blank/reserved pages need only their status. Routine filing covers need
      company, form, report/event period and optionally ticker; omit addresses,
      phone numbers, file/tax IDs, par values and checkboxes. For indexes, identify
      the index and broad destinations; indexed topics are references, not actual
      disclosures on this page. Retain substantive content if also present.
    </rules>

    <examples>
    Invented examples illustrate general rules; do not copy their facts.
    <example>
    Source: Opening Group liquidity discussion, 2033. Heading: Renewable Services.
    Its table lists revenue for 2032 and 2033, and contract backlog for 2033 only.
    A following "Year ended 2033" subheading discusses project delivery.
    Output: {{"summary": "Group liquidity, 2033; Renewable Services revenue, 2032-2033; contract backlog, 2033; project delivery, year ended 2033."}}
    </example>
    <example>
    Source: Regulatory clearance of LUMERA System; ORION study data; a $4 billion
    Meridian acquisition; a $600 million repurchase program announced June 2034;
    a 40% stake in Nova; a credit facility maturing September 2037.
    Output: {{"summary": "Regulatory clearance: LUMERA System; study data: ORION; acquisition: Meridian; share repurchase program announced June 2034; ownership interest in Nova; credit facility maturing September 2037."}}
    </example>
    <example>
    Source: Routine Example Manufacturing Form 10-K cover, fiscal year ended
    December 31, 2034, ticker EXM; address, filing checkboxes and stock par value.
    Output: {{"summary": "Example Manufacturing Form 10-K cover; fiscal year ended December 31, 2034; ticker EXM."}}
    </example>
    </examples>

    <page_data>
    {context}
    </page_data>

    Return only a completed JSON object matching this schema:
    {json.dumps(summary_schema)}
    """.strip()


def llm_call(xml_text, prompt):
    # Implement your LLM call here and return {"summary": "..."}.
    raise NotImplementedError("Add your LLM call here.")


final_chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))

# Fill only missing summaries; failed calls stay empty for the next run.
# Save after each success via a temporary file, then replace the original JSON.
for chunk in final_chunks:
    if chunk.get("summary") not in (None, ""):
        continue

    try:
        prompt = summary_prompt(chunk)
        result = llm_call(chunk["xml_text"], prompt)
        summary = PageInventory.model_validate(result).summary

    except Exception as error:
        print(f"Failed {chunk['page_id']}: {error}")
        continue

    chunk["summary"] = summary

    # A save failure stops the loop so it cannot generate more unsaved summaries.
    temporary_file = CHUNKS_FILE.with_suffix(".tmp")
    temporary_file.write_text(
        json.dumps(final_chunks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_file.replace(CHUNKS_FILE)

    print(f"Saved: {chunk['page_id']}")
