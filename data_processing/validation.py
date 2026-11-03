"""Validate the complete chunk and audit contract before writing outputs."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from typing import Any

from .pages import PAGE_OMISSION_REASONS, page_omission_reason
from .text import deduplicate_texts, invalid_xml_character_counts, page_uid

CHUNK_FIELDS = {
    "document_name", "company", "fiscal_date", "fiscal_quarter", "fiscal_year",
    "document_type", "page_in_pdf", "doc_sections", "page_id",
    "continued_from_page_id", "continues_on_page_id", "has_document_index",
    "has_table", "tables", "uid", "summary", "plain_text", "xml_text",
}


def validate_output(chunks: list[dict[str, Any]], audits: list[dict[str, Any]]) -> None:
    by_document: dict[str, list[dict[str, Any]]] = defaultdict(list)
    page_ids: set[str] = set()
    uids: set[str] = set()
    table_ids: set[str] = set()
    for chunk in chunks:
        if set(chunk) != CHUNK_FIELDS:
            raise ValueError(
                f"Unexpected chunk fields; missing={sorted(CHUNK_FIELDS - set(chunk))}, "
                f"extra={sorted(set(chunk) - CHUNK_FIELDS)}"
            )
        if not isinstance(chunk["summary"], str):
            raise ValueError("summary must be a string; empty is valid before summarization")
        expected_page_id = f"{chunk['document_name']}:page:{chunk['page_in_pdf']}"
        if chunk["page_id"] != expected_page_id:
            raise ValueError(f"Invalid page_id: {chunk['page_id']}")
        by_document[chunk["document_name"]].append(chunk)
        if not chunk["plain_text"]:
            raise ValueError(f"Empty page must be omitted from chunks: {chunk['page_id']}")
        invalid_plain_text = invalid_xml_character_counts(chunk["plain_text"])
        if invalid_plain_text:
            raise ValueError(
                f"XML-invalid characters remain in plain text on {chunk['page_id']}: "
                f"{invalid_plain_text}"
            )
        root = ET.fromstring(chunk["xml_text"])
        if root.tag != "page" or root.attrib:
            raise ValueError("XML text must use a metadata-free <page> root")
        if any(element.attrib for element in root.iter("heading")):
            raise ValueError("Heading levels must not be exposed in structured text")
        if any(element.attrib for element in root.iter("table")):
            raise ValueError("Table opening tags must not expose internal metadata")
        if any(element.attrib for element in root.iter("document_index")):
            raise ValueError("Document-index tags must not expose internal metadata")
        if any(
            element.attrib or len(element) or (element.text or "").strip()
            for element in root.iter("picture")
        ):
            raise ValueError("Picture placeholders must remain empty <picture /> elements")
        if not isinstance(chunk.get("fiscal_year"), int):
            raise ValueError("fiscal_year must be an integer")
        fiscal_quarter = chunk.get("fiscal_quarter")
        if fiscal_quarter is not None and fiscal_quarter not in {1, 2, 3, 4}:
            raise ValueError("fiscal_quarter must be 1, 2, 3, 4, or null")
        fiscal_date = chunk.get("fiscal_date")
        if fiscal_date is not None:
            try:
                datetime.strptime(fiscal_date, "%Y-%m-%d")
            except ValueError as error:
                raise ValueError(f"Invalid fiscal_date: {fiscal_date}") from error
        page = chunk["page_in_pdf"]
        expected_previous = f"{chunk['document_name']}:page:{page - 1}"
        expected_next = f"{chunk['document_name']}:page:{page + 1}"
        if chunk["continued_from_page_id"] not in {None, expected_previous}:
            raise ValueError(f"Invalid continued_from_page_id on {chunk['page_id']}")
        if chunk["continues_on_page_id"] not in {None, expected_next}:
            raise ValueError(f"Invalid continues_on_page_id on {chunk['page_id']}")
        if not isinstance(chunk.get("has_document_index"), bool):
            raise ValueError("has_document_index must be Boolean")
        xml_document_index_count = sum(1 for _ in root.iter("document_index"))
        if chunk["has_document_index"] != bool(xml_document_index_count):
            raise ValueError(
                f"has_document_index/XML mismatch on {chunk['page_id']}: "
                f"{chunk['has_document_index']} versus {xml_document_index_count} indexes"
            )
        if not isinstance(chunk.get("has_table"), bool):
            raise ValueError("has_table must be Boolean")
        tables = chunk.get("tables")
        if not isinstance(tables, list):
            raise ValueError("tables must always be a list")
        if chunk["has_table"] != bool(tables):
            raise ValueError("has_table must equal whether ordinary table records exist")
        omission_reason = page_omission_reason(
            chunk["plain_text"],
            has_table_block=chunk["has_table"] or chunk["has_document_index"],
        )
        if omission_reason is not None:
            raise ValueError(
                f"Non-substantive page must be omitted from chunks: "
                f"{chunk['page_id']} ({omission_reason})"
            )
        xml_table_count = sum(1 for _ in root.iter("table"))
        if len(tables) != xml_table_count:
            raise ValueError(
                f"Table catalogue/XML mismatch on {chunk['page_id']}: "
                f"{len(tables)} records versus {xml_table_count} tables"
            )
        for ordinal, table in enumerate(tables, start=1):
            if set(table) != {"table_id", "column_headers", "table_terms"}:
                raise ValueError(f"Invalid table catalogue object: {table}")
            expected_table_id = f"{chunk['page_id']}:table:{ordinal}"
            if table["table_id"] != expected_table_id:
                raise ValueError(
                    f"Unexpected table ID {table['table_id']}; expected {expected_table_id}"
                )
            if table["table_id"] in table_ids:
                raise ValueError(f"Duplicate table ID: {table['table_id']}")
            table_ids.add(table["table_id"])
            headers = table["column_headers"]
            terms = table["table_terms"]
            if not isinstance(headers, list) or not isinstance(terms, list):
                raise ValueError("column_headers and table_terms must be lists")
            if headers != deduplicate_texts(headers):
                raise ValueError(f"Invalid or duplicate column headers: {headers}")
            if terms != deduplicate_texts(terms):
                raise ValueError(f"Invalid or duplicate table terms: {terms}")
            overlap = {value.casefold() for value in headers}.intersection(
                value.casefold() for value in terms
            )
            if overlap:
                raise ValueError(f"Headers repeated as table terms: {sorted(overlap)}")
        if not isinstance(chunk.get("doc_sections"), list):
            raise ValueError("doc_sections must always be a list")
        seen_doc_sections: set[str] = set()
        seen_sec_items: set[tuple[str | None, str]] = set()
        for section in chunk["doc_sections"]:
            if set(section) != {
                "sec_item",
                "doc_section",
                "doc_part",
                "doc_section_start_page",
                "doc_section_end_page",
            }:
                raise ValueError(f"Invalid doc_sections object: {section}")
            sec_item = section["sec_item"]
            if not isinstance(sec_item, str) or not re.fullmatch(
                r"\d+(?:\.\d+)?[A-Z]?", sec_item, re.IGNORECASE
            ):
                raise ValueError("sec_item must be one SEC Item string")
            section_name = section["doc_section"]
            if not isinstance(section_name, str) or not section_name.strip():
                raise ValueError("doc_section must be one nonempty string")
            if section_name in seen_doc_sections:
                raise ValueError(f"Repeated doc_section on one page: {section_name}")
            seen_doc_sections.add(section_name)
            part = section["doc_part"]
            if part is not None and not re.fullmatch(r"PART\s+[IVX]+", part):
                raise ValueError(f"Invalid doc_part: {part}")
            item_key = (part, sec_item.upper())
            if item_key in seen_sec_items:
                raise ValueError(f"Repeated sec_item on one page: {item_key}")
            seen_sec_items.add(item_key)
            start_page = section["doc_section_start_page"]
            end_page = section["doc_section_end_page"]
            if not (
                isinstance(start_page, int)
                and isinstance(end_page, int)
                and 1 <= start_page <= chunk["page_in_pdf"] <= end_page
            ):
                raise ValueError(f"Invalid section page range: {section}")
        if chunk["page_id"] in page_ids:
            raise ValueError(f"Duplicate page_id: {chunk['page_id']}")
        page_ids.add(chunk["page_id"])
        expected_uid = page_uid(
            chunk["document_name"], chunk["page_in_pdf"], chunk["plain_text"]
        )
        if chunk.get("uid") != expected_uid:
            raise ValueError(
                f"UID does not match canonical plain text on {chunk['page_id']}: "
                f"{chunk.get('uid')!r} versus {expected_uid!r}"
            )
        if chunk["uid"] in uids:
            raise ValueError(f"Duplicate final UID: {chunk['uid']}")
        uids.add(chunk["uid"])

    chunks_by_page_id = {chunk["page_id"]: chunk for chunk in chunks}
    for chunk in chunks:
        previous_id = chunk["continued_from_page_id"]
        next_id = chunk["continues_on_page_id"]
        if previous_id is not None:
            previous = chunks_by_page_id.get(previous_id)
            if previous is None or previous["continues_on_page_id"] != chunk["page_id"]:
                raise ValueError(f"Continuation link is not bidirectional: {previous_id}")
        if next_id is not None:
            following = chunks_by_page_id.get(next_id)
            if following is None or following["continued_from_page_id"] != chunk["page_id"]:
                raise ValueError(f"Continuation link is not bidirectional: {next_id}")

    for audit in audits:
        document_chunks = by_document[audit["document_name"]]
        sanitization_by_page = audit["construction"]["xml_sanitization_by_page"]
        sanitization_total = sum(
            sum(code_points.values()) for code_points in sanitization_by_page.values()
        )
        if sanitization_total != audit["construction"]["xml_sanitization_total"]:
            raise ValueError(
                f"XML sanitization audit total is inconsistent for {audit['document_name']}"
            )
        expected = audit["physical_page_count"]
        page_numbers = [chunk["page_in_pdf"] for chunk in document_chunks]
        if page_numbers != sorted(page_numbers) or len(page_numbers) != len(set(page_numbers)):
            raise ValueError(f"Unordered or duplicate emitted pages for {audit['document_name']}")
        omitted_pages = audit.get("omitted_pages")
        if not isinstance(omitted_pages, list):
            raise ValueError(f"Invalid omitted-page audit for {audit['document_name']}")
        omitted_page_ids: list[str] = []
        omitted_reason_counts: dict[str, int] = defaultdict(int)
        for omitted_page in omitted_pages:
            if not isinstance(omitted_page, dict) or set(omitted_page) != {"page_id", "reason"}:
                raise ValueError(f"Invalid omitted-page record: {omitted_page!r}")
            omitted_page_id = omitted_page["page_id"]
            reason = omitted_page["reason"]
            if reason not in PAGE_OMISSION_REASONS:
                raise ValueError(f"Invalid omitted-page reason: {reason!r}")
            omitted_page_ids.append(omitted_page_id)
            omitted_reason_counts[reason] += 1
        if len(omitted_page_ids) != len(set(omitted_page_ids)):
            raise ValueError(f"Duplicate omitted pages for {audit['document_name']}")
        omitted_page_numbers: list[int] = []
        for omitted_page_id in omitted_page_ids:
            expected_prefix = f"{audit['document_name']}:page:"
            if not isinstance(omitted_page_id, str) or not omitted_page_id.startswith(
                expected_prefix
            ):
                raise ValueError(f"Invalid omitted page_id: {omitted_page_id!r}")
            omitted_page_numbers.append(int(omitted_page_id.removeprefix(expected_prefix)))
        if set(page_numbers).intersection(omitted_page_numbers):
            raise ValueError(f"Emitted and omitted pages overlap for {audit['document_name']}")
        if sorted(page_numbers + omitted_page_numbers) != list(range(1, expected + 1)):
            raise ValueError(f"Incomplete physical-page coverage for {audit['document_name']}")
        if audit.get("output_chunk_count") != len(document_chunks):
            raise ValueError(f"Incorrect output chunk count for {audit['document_name']}")
        if audit.get("omitted_page_count") != len(omitted_page_ids):
            raise ValueError(f"Incorrect omitted page count for {audit['document_name']}")
        if audit.get("omitted_page_reason_counts") != dict(omitted_reason_counts):
            raise ValueError(f"Incorrect omitted-page reason counts for {audit['document_name']}")
        if audit.get("physical_page_coverage_complete") is not True:
            raise ValueError(f"Physical-page audit failed for {audit['document_name']}")
