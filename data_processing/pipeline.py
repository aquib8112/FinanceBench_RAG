"""Build clean page chunks and a construction audit from one Docling document."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .docling import derive_page_continuations
from .metadata import FISCAL_DATE_CATALOG_PATH, parse_document_metadata
from .pages import (
    build_pages,
    page_content_kind,
    page_omission_reason,
    render_page_plain_text,
    render_page_xml,
)
from .sections import derive_section_boundaries, metadata_for_page
from .tables import page_table_catalog
from .text import page_uid


def build_document(
    document: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    metadata = parse_document_metadata(document["name"])
    pages, construction_audit = build_pages(document)
    section_boundaries = derive_section_boundaries(document)
    continuation_edges, continuation_audit = derive_page_continuations(document)

    chunks = []
    content_kind_counts = Counter()
    omitted_pages = []
    for physical_page, blocks in pages.items():
        page_id = f"{document['name']}:page:{physical_page}"
        plain_text = render_page_plain_text(blocks)
        content_kind_counts[page_content_kind(blocks)] += 1
        omission_reason = page_omission_reason(
            plain_text,
            has_table_block=any(block["type"] == "table" for block in blocks),
        )
        if omission_reason is not None:
            omitted_pages.append({"page_id": page_id, "reason": omission_reason})
            continue

        tables = page_table_catalog(blocks, page_id)
        chunks.append({
            **metadata,
            "page_in_pdf": physical_page,
            "doc_sections": metadata_for_page(section_boundaries, physical_page),
            "page_id": page_id,
            "continued_from_page_id": (
                f"{document['name']}:page:{physical_page - 1}"
                if (physical_page - 1, physical_page) in continuation_edges
                else None
            ),
            "continues_on_page_id": (
                f"{document['name']}:page:{physical_page + 1}"
                if (physical_page, physical_page + 1) in continuation_edges
                else None
            ),
            "has_document_index": any(
                block["type"] == "table" and block.get("label") == "document_index"
                for block in blocks
            ),
            "has_table": bool(tables),
            "tables": tables,
            "uid": page_uid(document["name"], physical_page, plain_text),
            "summary": "",
            "plain_text": plain_text,
            "xml_text": render_page_xml(blocks),
        })

    physical_page_count = len(pages)
    emitted_page_numbers = [chunk["page_in_pdf"] for chunk in chunks]
    omitted_page_numbers = [int(page["page_id"].rsplit(":page:", 1)[1]) for page in omitted_pages]
    audit = {
        "document_name": document["name"],
        "physical_page_count": physical_page_count,
        "output_chunk_count": len(chunks),
        "omitted_page_count": len(omitted_pages),
        "omitted_pages": omitted_pages,
        "omitted_page_reason_counts": dict(Counter(page["reason"] for page in omitted_pages)),
        "physical_page_coverage_complete": sorted(emitted_page_numbers + omitted_page_numbers)
        == list(range(1, physical_page_count + 1)),
        "content_kind_counts": dict(content_kind_counts),
        "pages_with_document_index": sum(chunk["has_document_index"] for chunk in chunks),
        "pages_with_ordinary_tables": sum(chunk["has_table"] for chunk in chunks),
        "ordinary_table_catalog_count": sum(len(chunk["tables"]) for chunk in chunks),
        "section_metadata": {
            "toc_entry_count": section_boundaries["toc_entry_count"],
            "real_section_count": len(section_boundaries["sections"]),
            "classification_counts": section_boundaries["classification_counts"],
            "pages_with_multiple_sections": len(section_boundaries["pages_with_multiple_sections"]),
        },
        "period_metadata": {
            "fiscal_year": metadata["fiscal_year"],
            "fiscal_quarter": metadata["fiscal_quarter"],
            "fiscal_date": metadata["fiscal_date"],
            "fiscal_date_source": FISCAL_DATE_CATALOG_PATH.name,
        },
        "continuation_metadata": continuation_audit,
        "construction": construction_audit,
    }
    return chunks, audit
