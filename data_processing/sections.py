"""Derive fail-closed SEC Part/Item boundaries from Docling documents.

The source of truth is visible filing text: TOC Item rows when available and
ordered body headings otherwise. PDF destinations are deliberately not used.
Printed TOC pages are used only when Docling did not retain a usable heading.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from typing import Any, Iterable

from .section_matching import (
    PART_RE,
    anchored_rows,
    extract_toc_entries,
    form_for_name,
    heading_candidates,
    heading_nodes,
    match_entry,
    normalize,
    numeric_page_footers,
    parse_item_marker,
    valid_item_number,
)


HEADING_LABELS = {"section_header", "page_header"}
ITEM_WORD_RE = re.compile(r"\bITEM(S)?\s+", re.IGNORECASE)
ITEM_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?[A-Z]?", re.IGNORECASE)
PAGE_TOKEN_RE = re.compile(r"^\s*(\d+)(?:\s*[-â€“â€”]\s*(\d+))?\s*$")
PART_PREFIX_RE = re.compile(r"^\s*PART\s+([IVX]+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class BodyItemCandidate:
    part: str | None
    items: tuple[str, ...]
    title: str
    text: str
    normalized_title: str
    page: int
    vertical: float
    text_index: int
    provenance_index: int
    label: str
    source_span_id: str
    fused_part_prefix: bool
    combined: bool

    @property
    def position(self) -> tuple[int, float, int, int]:
        return self.page, self.vertical, self.text_index, self.provenance_index


def form_for_document(document: dict[str, Any]) -> str:
    return form_for_name(str(document.get("name", "")))


def part_for_10k_item(item: str) -> str | None:
    """Return the standard Form 10-K Part for an Item identity."""

    leading_match = re.match(r"\d+", item)
    if not leading_match:
        return None
    leading = int(leading_match.group())
    if leading <= 4:
        return "I"
    if leading <= 9:
        return "II"
    if leading <= 14:
        return "III"
    if leading <= 16:
        return "IV"
    return None


def canonical_part(form: str, item: str, parsed_part: str | None) -> str | None:
    if form == "10K":
        return part_for_10k_item(item)
    if form == "10Q":
        return parsed_part
    return None


def display_part(part: str | None) -> str | None:
    return f"PART {part}" if part else None


def clean_source_title(value: str) -> str:
    value = re.split(PART_RE, value, maxsplit=1)[0]
    value = re.sub(r"\s+", " ", value)
    return value.strip(" .:-â€“â€”")


def display_section(item: str, title: str) -> str:
    title = clean_source_title(title)
    return f"Item {item}. {title}".rstrip()


def provenance_vertical(prov: dict[str, Any]) -> float:
    bbox = prov.get("bbox") or {}
    if bbox.get("coord_origin") == "TOPLEFT":
        return float(bbox.get("t", 0.0))
    if bbox.get("coord_origin") == "BOTTOMLEFT":
        return -float(bbox.get("t", 0.0))
    return 0.0


def toc_physical_pages(document: dict[str, Any]) -> set[int]:
    return {
        int(table["prov"][0]["page_no"])
        for table in document.get("tables", [])
        if table.get("label") == "document_index"
        and table.get("prov")
        and int(table["prov"][0]["page_no"]) <= 5
    }


def parse_leading_item_text(text: str, form: str) -> tuple[str | None, tuple[str, ...], str, bool] | None:
    """Parse a body string beginning with Item or a fused Part ... Item."""

    text = " ".join(text.split())
    prefix_part: str | None = None
    fused = False
    if PART_PREFIX_RE.match(text):
        prefix_part = PART_PREFIX_RE.match(text).group(1).upper()
        item_word = ITEM_WORD_RE.search(text)
        if item_word is None:
            return None
        fused = True
    else:
        item_word = ITEM_WORD_RE.match(text)
        if item_word is None:
            return None

    plural = bool(item_word.group(1))
    remainder = text[item_word.end() :]
    if plural:
        # Combined source headings in this corpus use a period between the
        # number list and the semicolon-separated titles.
        number_text, separator, title = remainder.partition(".")
        if not separator:
            return None
        items = tuple(value.upper() for value in ITEM_NUMBER_RE.findall(number_text))
    else:
        marker = re.match(r"(\d+(?:\.\d+)?[A-Z]?)\.?\s*(.*)$", remainder, re.IGNORECASE)
        if marker is None:
            return None
        items = (marker.group(1).upper(),)
        title = marker.group(2)

    if not items or any(not valid_item_number(item, form) for item in items):
        return None
    return prefix_part, items, clean_source_title(title), fused


def body_item_candidates(document: dict[str, Any], form: str) -> list[BodyItemCandidate]:
    """Return leading Item candidates with geometry-aware 10-Q Part scope."""

    toc_pages = toc_physical_pages(document)
    provisional: list[dict[str, Any]] = []
    part_markers: list[tuple[tuple[int, float, int, int], str]] = []

    for text_index, obj in enumerate(document.get("texts", [])):
        label = str(obj.get("label", ""))
        text = " ".join(str(obj.get("text", "")).split())
        if not text:
            continue
        parsed = parse_leading_item_text(text, form)
        for provenance_index, prov in enumerate(obj.get("prov", [])):
            page = int(prov["page_no"])
            if page in toc_pages:
                continue
            position = (page, provenance_vertical(prov), text_index, provenance_index)
            if label in HEADING_LABELS:
                part_match = PART_RE.search(text)
                if part_match:
                    part_markers.append((position, part_match.group(1).upper()))
            if parsed is None:
                continue
            prefix_part, items, title, fused = parsed
            provisional.append(
                {
                    "prefix_part": prefix_part,
                    "items": items,
                    "title": title,
                    "text": text,
                    "page": page,
                    "vertical": position[1],
                    "text_index": text_index,
                    "provenance_index": provenance_index,
                    "label": label,
                    "source_span_id": f"#/texts/{text_index}:prov/{provenance_index}",
                    "fused": fused,
                    "combined": len(items) > 1,
                    "position": position,
                }
            )

    part_markers.sort()
    part_ii_positions = [position for position, part in part_markers if part == "II"]
    part_ii_boundary = part_ii_positions[0] if part_ii_positions else None
    candidates: list[BodyItemCandidate] = []
    for item in provisional:
        parsed_part = item["prefix_part"]
        if form == "10Q" and parsed_part is None:
            if part_ii_boundary is None or item["page"] < part_ii_boundary[0]:
                parsed_part = "I"
            elif item["page"] > part_ii_boundary[0]:
                parsed_part = "II"
            else:
                # Two-column filings can place a later right-column Item above
                # the left-column Part II marker. Accept either Docling source
                # order or vertical order as evidence that the marker precedes
                # the Item on this shared transition page.
                after_in_source = item["text_index"] >= part_ii_boundary[2]
                after_vertically = item["vertical"] >= part_ii_boundary[1]
                parsed_part = "II" if after_in_source or after_vertically else "I"
        for number in item["items"]:
            part = canonical_part(form, number, parsed_part)
            candidates.append(
                BodyItemCandidate(
                    part=part,
                    items=item["items"],
                    title=item["title"],
                    text=item["text"],
                    normalized_title=normalize(item["title"]),
                    page=item["page"],
                    vertical=item["vertical"],
                    text_index=item["text_index"],
                    provenance_index=item["provenance_index"],
                    label=item["label"],
                    source_span_id=item["source_span_id"],
                    fused_part_prefix=item["fused"],
                    combined=item["combined"],
                )
            )
    return candidates


def toc_auxiliary_evidence(document: dict[str, Any], form: str) -> dict[tuple[str | None, str], dict[str, Any]]:
    """Collect N/A markers, child pages, and printed page ranges from TOC rows."""

    evidence: dict[tuple[str | None, str], dict[str, Any]] = defaultdict(
        lambda: {"not_applicable": False, "child_pages": [], "range_starts": []}
    )
    current_part: str | None = None
    current_key: tuple[str | None, str] | None = None
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

    for table in tables:
        source_page = int(table["prov"][0]["page_no"])
        for cells in anchored_rows(table):
            values = [" ".join(str(cell.get("text", "")).split()) for cell in cells]
            nonempty = [value for value in values if value]
            first = nonempty[0] if nonempty else ""
            marker = parse_item_marker(first, form, allow_bare=source_page <= 5)
            row_text = " ".join(values)

            if marker is None:
                part_match = PART_RE.search(row_text)
                if part_match:
                    current_part = part_match.group(1).upper()
                    current_key = None
                    continue
                if current_key is not None:
                    if any(value.upper() == "N/A" for value in values):
                        evidence[current_key]["not_applicable"] = True
                    for value in values:
                        page_match = PAGE_TOKEN_RE.fullmatch(value)
                        if page_match:
                            evidence[current_key]["child_pages"].append(int(page_match.group(1)))
                continue

            item, _ = marker
            key_part = current_part if form == "10Q" else None
            current_key = (key_part, item)
            if any(value.upper() == "N/A" for value in values):
                evidence[current_key]["not_applicable"] = True
            for value in values:
                page_match = PAGE_TOKEN_RE.fullmatch(value)
                if page_match and page_match.group(2):
                    evidence[current_key]["range_starts"].append(int(page_match.group(1)))

            # Some malformed rows append the following Part marker after the
            # current Item. It applies only to subsequent rows.
            part_match = PART_RE.search(row_text)
            if part_match:
                current_part = part_match.group(1).upper()

    return dict(evidence)


def invert_numeric_footers(document: dict[str, Any]) -> dict[int, list[int]]:
    result: dict[int, list[int]] = defaultdict(list)
    for physical_page, printed_pages in numeric_page_footers(document).items():
        for printed_page in printed_pages:
            result[printed_page].append(physical_page)
    return {printed: sorted(pages) for printed, pages in result.items()}


def choose_printed_page(printed_page: int | None, footer_pages: dict[int, list[int]], toc_pages: set[int]) -> int | None:
    if printed_page is None:
        return None
    candidates = [page for page in footer_pages.get(printed_page, []) if page not in toc_pages]
    return candidates[0] if len(candidates) == 1 else None


def item_order_key(part: str | None, item: str) -> tuple[int, int, int, str]:
    roman_order = {None: 0, "I": 1, "II": 2, "III": 3, "IV": 4}
    match = re.match(r"(\d+)(?:\.(\d+))?([A-Z]?)", item, re.IGNORECASE)
    if match is None:
        return roman_order.get(part, 9), 999, 999, item
    leading = int(match.group(1))
    decimal = int(match.group(2) or 0)
    suffix = match.group(3).upper()
    return roman_order.get(part, 9), leading, decimal, suffix


def dedupe_candidates(candidates: Iterable[BodyItemCandidate]) -> list[BodyItemCandidate]:
    unique: dict[tuple[str, str | None], BodyItemCandidate] = {}
    for candidate in candidates:
        unique[(candidate.source_span_id, candidate.part)] = candidate
    return sorted(unique.values(), key=lambda candidate: candidate.position)


def select_candidate(
    candidates: list[BodyItemCandidate],
    *,
    part: str | None,
    item: str,
    page: int | None = None,
    heading_only: bool = False,
) -> BodyItemCandidate | None:
    selected = [
        candidate
        for candidate in candidates
        if item in candidate.items
        and candidate.part == part
        and (page is None or candidate.page == page)
        and (not heading_only or candidate.label in HEADING_LABELS)
    ]
    selected = dedupe_candidates(selected)
    if len(selected) == 1:
        return selected[0]
    if selected:
        titled_headings = [
            candidate
            for candidate in selected
            if candidate.label == "section_header" and candidate.title
        ]
        titled_headings = dedupe_candidates(titled_headings)
        if len(titled_headings) == 1:
            return titled_headings[0]
    return None


def _entry_key(form: str, entry: dict[str, Any]) -> tuple[str | None, str]:
    part = canonical_part(form, entry["item"], entry.get("part"))
    return part, entry["item"]


def derive_section_boundaries(document: dict[str, Any]) -> dict[str, Any]:
    """Return audited Item boundaries and non-present/unresolved TOC entries."""

    form = form_for_document(document)
    page_count = len(document.get("pages", {}))
    if form == "EARNINGS":
        return {
            "document_name": document.get("name"),
            "form": form,
            "physical_page_count": page_count,
            "toc_entry_count": 0,
            "classification_counts": {},
            "entries": [],
            "sections": [],
            "pages_with_multiple_sections": [],
        }

    toc_entries = extract_toc_entries(document, form)
    toc_pages = toc_physical_pages(document)
    auxiliary = toc_auxiliary_evidence(document, form)
    footer_pages = invert_numeric_footers(document)
    direct_candidates = body_item_candidates(document, form)

    if form == "10Q":
        # A few Docling body files lose the standalone PART II heading even
        # though the TOC retains it. Recover scope only when Item number and
        # complete normalized title select one TOC identity; Item number alone
        # remains forbidden because Parts I and II reuse numbers.
        toc_parts_by_item_title: dict[tuple[str, str], set[str | None]] = defaultdict(set)
        for entry in toc_entries:
            toc_parts_by_item_title[(entry["item"], normalize(entry.get("title", "")))].add(
                entry.get("part")
            )
        remapped_candidates: list[BodyItemCandidate] = []
        for candidate in direct_candidates:
            if len(candidate.items) == 1:
                possible_parts = toc_parts_by_item_title.get(
                    (candidate.items[0], candidate.normalized_title), set()
                )
                if len(possible_parts) == 1:
                    candidate = replace(candidate, part=next(iter(possible_parts)))
            remapped_candidates.append(candidate)
        direct_candidates = remapped_candidates

    section_nodes = heading_nodes(document, form, {"section_header"})
    section_candidates = heading_candidates(section_nodes)
    heading_like_nodes = heading_nodes(document, form, HEADING_LABELS)
    heading_like_candidates = heading_candidates(heading_like_nodes)
    all_nodes = heading_nodes(document, form, None)
    all_candidates = heading_candidates(all_nodes)

    classified_entries: list[dict[str, Any]] = []
    toc_keys: set[tuple[str | None, str]] = set()
    for toc_order, entry in enumerate(toc_entries):
        key = _entry_key(form, entry)
        part, item = key
        toc_keys.add(key)
        heading_like = match_entry(entry, heading_like_nodes, heading_like_candidates, form)
        all_text = match_entry(entry, all_nodes, all_candidates, form)
        primary = match_entry(entry, section_nodes, section_candidates, form)
        aux_key = (entry.get("part") if form == "10Q" else None, item)
        aux = auxiliary.get(aux_key, {})

        match_type = "unresolved"
        start_page: int | None = None
        source_candidate: BodyItemCandidate | None = None

        if heading_like["full_match_count"] == 1:
            match_type = "exact_heading"
            start_page = heading_like["full_match_pages"][0]
            source_candidate = select_candidate(
                direct_candidates, part=part, item=item, page=start_page, heading_only=True
            )
        elif all_text["full_match_count"] == 1:
            match_type = "exact_other_label"
            start_page = all_text["full_match_pages"][0]
            source_candidate = select_candidate(
                direct_candidates, part=part, item=item, page=start_page
            )
        elif primary["part_scoped_item_heading_count"] == 1:
            match_type = "normalized_heading"
            start_page = primary["part_scoped_item_heading_pages"][0]
            source_candidate = select_candidate(
                direct_candidates, part=part, item=item, page=start_page, heading_only=True
            )
        else:
            candidate = select_candidate(direct_candidates, part=part, item=item)
            if candidate is not None:
                source_candidate = candidate
                start_page = candidate.page
                match_type = "combined_heading" if candidate.combined else "normalized_heading"

        if start_page is None and primary["title_heading_pages"]:
            printed_page = entry.get("printed_page")
            confirmed = [
                page
                for page in primary["title_heading_pages"]
                if printed_page is not None and page in footer_pages.get(printed_page, [])
            ]
            if len(confirmed) == 1:
                start_page = confirmed[0]
                match_type = "normalized_heading"

        explicitly_absent = bool(aux.get("not_applicable")) or (
            normalize(entry.get("title", "")) in {"removed and reserved", "removed", "reserved"}
            and entry.get("printed_page") is None
            and start_page is None
        )
        if start_page is None and explicitly_absent:
            match_type = "not_present"

        if start_page is None and match_type == "unresolved":
            range_starts = sorted(set(aux.get("range_starts", [])))
            inferred_printed = range_starts[0] if range_starts else entry.get("printed_page")
            inferred_physical = choose_printed_page(inferred_printed, footer_pages, toc_pages)
            if inferred_physical is not None:
                start_page = inferred_physical
                match_type = "page_inferred"

        if start_page is None and match_type == "unresolved":
            child_pages = sorted(set(aux.get("child_pages", [])))
            child_physical = choose_printed_page(
                child_pages[0] if child_pages else None, footer_pages, toc_pages
            )
            if child_physical is not None:
                start_page = child_physical
                match_type = "child_toc_page"

        classified_entries.append(
            {
                "toc_order": toc_order,
                "part": part,
                "item": item,
                "title": clean_source_title(entry.get("title", "")),
                "doc_part": display_part(part),
                "doc_section": display_section(item, entry.get("title", "")),
                "printed_page": entry.get("printed_page"),
                "start_page": start_page,
                "match_type": match_type,
                "source_span_id": source_candidate.source_span_id if source_candidate else None,
                "source_heading": source_candidate.text if source_candidate else None,
                "source_label": source_candidate.label if source_candidate else None,
            }
        )

    # Recover real body Items that Docling merged into another TOC row or that
    # occur in filings without an SEC Item TOC. Discovery is heading-like only;
    # ordinary prose can validate an existing TOC identity but cannot invent one.
    supplemental_by_key: dict[tuple[str | None, str], list[BodyItemCandidate]] = defaultdict(list)
    for candidate in direct_candidates:
        if candidate.label not in HEADING_LABELS or not candidate.title:
            continue
        for item in candidate.items:
            key = (candidate.part, item)
            if key not in toc_keys:
                supplemental_by_key[key].append(candidate)

    supplemental_entries: list[dict[str, Any]] = []
    for (part, item), candidates in supplemental_by_key.items():
        selected = select_candidate(candidates, part=part, item=item, heading_only=True)
        if selected is None:
            continue
        supplemental_entries.append(
            {
                "toc_order": None,
                "part": part,
                "item": item,
                "title": selected.title,
                "doc_part": display_part(part),
                "doc_section": display_section(item, selected.title),
                "printed_page": None,
                "start_page": selected.page,
                "match_type": "direct_body_heading",
                "source_span_id": selected.source_span_id,
                "source_heading": selected.text,
                "source_label": selected.label,
            }
        )

    classified_entries.extend(supplemental_entries)
    real_sections = [entry for entry in classified_entries if entry["start_page"] is not None]
    real_sections.sort(
        key=lambda entry: (
            int(entry["start_page"]),
            item_order_key(entry["part"], entry["item"]),
            entry["source_span_id"] or "",
        )
    )

    # Several Item aliases can honestly share one source heading and range.
    boundary_groups: list[list[dict[str, Any]]] = []
    for entry in real_sections:
        span_key = entry["source_span_id"] or f"page:{entry['start_page']}:item:{entry['part']}:{entry['item']}"
        if boundary_groups:
            previous = boundary_groups[-1][0]
            previous_key = previous["source_span_id"] or (
                f"page:{previous['start_page']}:item:{previous['part']}:{previous['item']}"
            )
            if span_key == previous_key:
                boundary_groups[-1].append(entry)
                continue
        boundary_groups.append([entry])

    for index, group in enumerate(boundary_groups):
        start_page = int(group[0]["start_page"])
        if index + 1 < len(boundary_groups):
            next_start = int(boundary_groups[index + 1][0]["start_page"])
            end_page = start_page if next_start == start_page else next_start - 1
        else:
            end_page = page_count
        for entry in group:
            entry["end_page"] = end_page

    page_membership: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for section in real_sections:
        for page in range(int(section["start_page"]), int(section["end_page"]) + 1):
            page_membership[page].append(section)
    pages_with_multiple = [
        {
            "page": page,
            "sections": [section["doc_section"] for section in sections],
        }
        for page, sections in sorted(page_membership.items())
        if len(sections) > 1
    ]

    classification_counts = Counter(entry["match_type"] for entry in classified_entries)
    return {
        "document_name": document.get("name"),
        "form": form,
        "physical_page_count": page_count,
        "toc_entry_count": len(toc_entries),
        "classification_counts": dict(classification_counts),
        "entries": classified_entries,
        "sections": real_sections,
        "pages_with_multiple_sections": pages_with_multiple,
    }


def metadata_for_page(boundaries: dict[str, Any], page: int) -> list[dict[str, Any]]:
    """Return one metadata object per SEC Item covering a physical page."""

    result: list[dict[str, Any]] = []
    for section in boundaries.get("sections", []):
        start_page = int(section["start_page"])
        end_page = int(section["end_page"])
        if not start_page <= page <= end_page:
            continue
        result.append(
            {
                "sec_item": section["item"],
                "doc_section": section["doc_section"],
                "doc_part": section["doc_part"],
                "doc_section_start_page": start_page,
                "doc_section_end_page": end_page,
            }
        )
    return result
