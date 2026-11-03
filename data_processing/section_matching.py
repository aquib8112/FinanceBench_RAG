"""Production helpers for matching SEC table-of-contents entries to body headings."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Any

ITEM_RE = re.compile(r"^\s*ITEM\s+(\d+(?:\.\d+)?[A-Z]?)\.?\s*(.*)$", re.IGNORECASE)
BARE_ITEM_RE = re.compile(r"^(\d+(?:\.\d+)?[A-Z]?)\.?$", re.IGNORECASE)
PART_RE = re.compile(r"\bPART\s+([IVX]+)\b", re.IGNORECASE)
PAGE_RE = re.compile(r"^\s*(\d+)\s*$")

def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.replace("â€™", "'").replace("â€˜", "'").replace("ï¿½", " ")
    value = value.casefold().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def form_for_name(name: str) -> str:
    upper = name.upper()
    if "_10K" in upper:
        return "10K"
    if "_10Q" in upper:
        return "10Q"
    if "_8K" in upper:
        return "8K"
    return "EARNINGS"


def anchored_rows(table: dict[str, Any]) -> list[list[dict[str, Any]]]:
    rows: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for cell in table.get("data", {}).get("table_cells", []):
        rows[int(cell["start_row_offset_idx"])].append(cell)
    return [
        sorted(rows[index], key=lambda cell: int(cell["start_col_offset_idx"]))
        for index in range(int(table.get("data", {}).get("num_rows", 0)))
    ]


def valid_item_number(item: str, form: str) -> bool:
    leading = int(re.match(r"\d+", item).group())
    if form == "10K":
        return leading <= 16 and "." not in item
    if form == "10Q":
        return leading <= 6 and "." not in item
    if form == "8K":
        return leading <= 9 and "." in item
    return False


def parse_item_marker(value: str, form: str, allow_bare: bool) -> tuple[str, str] | None:
    value = " ".join(value.split())
    explicit = ITEM_RE.match(value)
    if explicit:
        item = explicit.group(1).upper()
        remainder = explicit.group(2).strip(" .:-â€“â€”")
        # `Item 4(a)` is a subentry, not SEC Item 4 repeated.
        if remainder.startswith("(") or not valid_item_number(item, form):
            return None
        return item, remainder
    if allow_bare:
        bare = BARE_ITEM_RE.fullmatch(value)
        if bare and valid_item_number(bare.group(1).upper(), form):
            return bare.group(1).upper(), ""
    return None


def clean_title(value: str) -> str:
    value = re.split(PART_RE, value, maxsplit=1)[0]
    return value.strip(" .:-â€“â€”")


def title_and_page(
    cells: list[dict[str, Any]], marker_remainder: str, *, skip_first_cell: bool = True
) -> tuple[str, int | None]:
    values = [" ".join(str(cell.get("text", "")).split()) for cell in cells]
    title_parts: list[str] = [marker_remainder] if marker_remainder else []
    printed_page: int | None = None
    for value in values[1:] if skip_first_cell else values:
        if not value:
            continue
        page_match = PAGE_RE.fullmatch(value)
        if page_match:
            printed_page = int(page_match.group(1))
            continue
        if normalize(value) in {"page", "beginning page"} or value.upper() == "N/A":
            continue
        title_parts.append(value)
    return clean_title(" ".join(title_parts)), printed_page


def extract_toc_entries(document: dict[str, Any], form: str) -> list[dict[str, Any]]:
    if form not in {"10K", "10Q", "8K"}:
        return []
    tables = sorted(
        (
            table
            for table in document.get("tables", [])
            if table.get("label") == "document_index"
            and table.get("prov")
            and int(table["prov"][0]["page_no"]) <= 5
        ),
        key=lambda table: int(table["prov"][0]["page_no"]),
    )
    entries: list[dict[str, Any]] = []
    current_part: str | None = None

    for table in tables:
        source_page = int(table["prov"][0]["page_no"])
        rows = anchored_rows(table)
        parsed: list[dict[str, Any]] = []
        for cells in rows:
            nonempty = [cell for cell in cells if str(cell.get("text", "")).strip()]
            first = " ".join(str(nonempty[0].get("text", "")).split()) if nonempty else ""
            marker = parse_item_marker(first, form, allow_bare=source_page <= 5)
            row_text = " ".join(str(cell.get("text", "")).strip() for cell in cells)

            # If an Item and the following Part marker were merged into one row,
            # the Item still belongs to the current Part. Update Part afterward.
            entry_part = current_part
            if marker is None:
                part_match = PART_RE.search(row_text)
                if part_match:
                    current_part = part_match.group(1).upper()

            part_after = (
                PART_RE.search(row_text).group(1).upper()
                if marker is not None and PART_RE.search(row_text)
                else None
            )
            parsed.append(
                {
                    "cells": cells,
                    "marker": marker,
                    "entry_part": entry_part,
                    "part_after": part_after,
                }
            )
            # A malformed Docling row can fuse the last Part I Item and the
            # following `PART II` marker. The marker applies to later rows, so
            # advance the parse state now; assigning it only in the later entry
            # construction pass leaves every following row scoped to Part I.
            if part_after:
                current_part = part_after

        for index, row in enumerate(parsed):
            marker = row["marker"]
            if marker is None:
                continue
            item, remainder = marker
            title, printed_page = title_and_page(row["cells"], remainder)

            # Some 10-Q indexes put `Item 1.` on one row and title/page on the
            # next. Use the first following descriptive row only.
            if not title:
                for following in parsed[index + 1 :]:
                    if following["marker"] is not None:
                        break
                    candidate, candidate_page = title_and_page(
                        following["cells"], "", skip_first_cell=False
                    )
                    if candidate:
                        title = candidate
                        printed_page = candidate_page
                        break

            part = row["entry_part"] if form == "10Q" else None
            entries.append(
                {
                    "part": part,
                    "item": item,
                    "title": title,
                    "printed_page": printed_page,
                    "toc_physical_page": source_page,
                }
            )
            if row["part_after"]:
                current_part = row["part_after"]

    # Continued TOC pages and malformed subentries can repeat an identity. Keep
    # the first substantive non-continued entry as the section definition.
    selected: dict[tuple[str | None, str], dict[str, Any]] = {}
    for entry in entries:
        key = (entry["part"], entry["item"])
        existing = selected.get(key)
        if existing is None:
            selected[key] = entry
            continue
        existing_continued = "continued" in normalize(existing["title"])
        new_continued = "continued" in normalize(entry["title"])
        if existing_continued and not new_continued:
            selected[key] = entry
    return list(selected.values())


def heading_nodes(
    document: dict[str, Any], form: str, labels: set[str] | None = None
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    current_part: str | None = "I" if form == "10Q" else None
    for index, obj in enumerate(document.get("texts", [])):
        if (labels is not None and obj.get("label") not in labels) or not obj.get("prov"):
            continue
        text = " ".join(obj.get("text", "").split())
        part_match = PART_RE.search(text)
        if part_match and not ITEM_RE.match(text):
            current_part = part_match.group(1).upper()
        for provenance_index, prov in enumerate(obj["prov"]):
            nodes.append(
                {
                    "text": text,
                    "normalized": normalize(text),
                    "page": int(prov["page_no"]),
                    "part": current_part if form == "10Q" else None,
                    "text_index": index,
                    "provenance_index": provenance_index,
                }
            )
    return nodes


def heading_candidates(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for start, node in enumerate(nodes):
        parts: list[str] = []
        for length in range(1, 4):
            end = start + length
            if end > len(nodes):
                break
            candidate_node = nodes[end - 1]
            if candidate_node["page"] != node["page"] or candidate_node["part"] != node["part"]:
                break
            parts.append(candidate_node["text"])
            candidates.append(
                {
                    "text": " ".join(parts),
                    "normalized": normalize(" ".join(parts)),
                    "page": node["page"],
                    "part": node["part"],
                    "start": start,
                    "length": length,
                }
            )
    return candidates


def unique_occurrences(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[int, int], dict[str, Any]] = {}
    for match in matches:
        unique[(match["page"], match["start"])] = match
    return list(unique.values())


def match_entry(
    entry: dict[str, Any], nodes: list[dict[str, Any]], candidates: list[dict[str, Any]], form: str
) -> dict[str, Any]:
    expected_full = normalize(f"Item {entry['item']} {entry['title']}")
    expected_title = normalize(entry["title"])
    expected_item = normalize(f"Item {entry['item']}")
    part = entry["part"] if form == "10Q" else None

    full = unique_occurrences(
        [
            candidate
            for candidate in candidates
            if candidate["normalized"] == expected_full
        ]
    )
    item_only = [
        node
        for node in nodes
        if (
            node["normalized"] == expected_item
            or node["normalized"].startswith(expected_item + " ")
        )
    ]
    part_scoped_item_only = [
        node
        for node in item_only
        if form != "10Q" or node["part"] == part
    ]
    title_only = unique_occurrences(
        [
            candidate
            for candidate in candidates
            if expected_title
            and candidate["normalized"] == expected_title
        ]
    )
    return {
        **entry,
        "expected_normalized": expected_full,
        "full_match_count": len(full),
        "full_match_pages": sorted({match["page"] for match in full}),
        "full_matches": [
            {"page": match["page"], "text": match["text"], "nodes": match["length"]}
            for match in full
        ],
        "item_heading_count": len(item_only),
        "item_heading_pages": sorted({node["page"] for node in item_only}),
        "part_scoped_item_heading_count": len(part_scoped_item_only),
        "part_scoped_item_heading_pages": sorted(
            {node["page"] for node in part_scoped_item_only}
        ),
        "title_heading_count": len(title_only),
        "title_heading_pages": sorted({match["page"] for match in title_only}),
    }


def numeric_page_footers(document: dict[str, Any]) -> dict[int, list[int]]:
    by_page: dict[int, set[int]] = defaultdict(set)
    for obj in document.get("texts", []):
        if obj.get("label") != "page_footer":
            continue
        match = PAGE_RE.fullmatch(" ".join(obj.get("text", "").split()))
        if not match:
            continue
        printed_page = int(match.group(1))
        for prov in obj.get("prov", []):
            by_page[int(prov["page_no"])].add(printed_page)
    return {page: sorted(values) for page, values in by_page.items()}
