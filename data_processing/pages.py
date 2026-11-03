"""Build and render one canonical chunk candidate per physical PDF page."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Any

from .docling import (
    should_remove_text,
    provenance_fragments,
    ref_section,
    resolve_ref,
)
from .tables import (
    layout_order_key,
    render_table_xml,
    table_owned_text_refs,
    table_payload,
)
from .text import (
    invalid_xml_character_counts,
    normalize_text,
    sanitize_xml_text,
    table_catalog_text,
)

PICTURE_TEXT_LABELS = {"caption", "footnote", "section_header"}
PAGE_OMISSION_REASONS = {"empty", "page_number_only", "filing_label_only"}
FILING_LABEL_ONLY_TEXTS = {"FORM 10-K", "FORM 10-Q"}


def page_omission_reason(plain_text: str, *, has_table_block: bool) -> str | None:
    """Return why a physical page has no useful standalone retrieval content."""

    text = normalize_text(plain_text).strip()
    if not text:
        return "empty"
    if has_table_block:
        return None
    if text.isdigit() and len(text) <= 4:
        return "page_number_only"
    if text.upper() in FILING_LABEL_ONLY_TEXTS:
        return "filing_label_only"
    return None


def block_tag(label: str | None) -> str:
    if label == "section_header":
        return "heading"
    if label == "list_item":
        return "list_item"
    if label in {"caption", "footnote", "page_header", "page_footer"}:
        return label
    return "text"


def restore_list_marker(obj: dict[str, Any], fragment: str, provenance_index: int) -> str:
    """Prepend a source list marker only where the logical item begins."""

    if obj.get("label") != "list_item":
        return fragment
    marker = str(obj.get("marker") or "").strip()
    if not marker:
        return fragment

    provenance = obj.get("prov") or []
    prov = provenance[provenance_index] if provenance_index < len(provenance) else {}
    charspan = prov.get("charspan")
    begins_item = int(charspan[0]) == 0 if charspan and len(charspan) == 2 else provenance_index == 0
    if not begins_item or fragment.lstrip().startswith(marker):
        return fragment
    return f"{marker} {fragment}"


def build_pages(
    document: dict[str, Any],
) -> tuple[dict[int, list[dict[str, Any]]], dict[str, Any]]:
    page_count = len(document.get("pages", {}))
    pages: dict[int, list[dict[str, Any]]] = {page: [] for page in range(1, page_count + 1)}
    audit: dict[str, Any] = {
        "removed_furniture": defaultdict(int),
        "xml_sanitization_by_page": defaultdict(lambda: defaultdict(int)),
        "ignored_picture_text_by_page": defaultdict(int),
        "picture_markers_by_page": defaultdict(int),
        "preserved_picture_text_by_label": defaultdict(int),
        "restored_table_text_by_label": defaultdict(int),
        "restored_table_text_by_position": defaultdict(int),
        "table_conflicts": [],
        "unprovenanced_refs": [],
    }
    restored_table_text_refs: set[str] = set()

    def sanitize_page_text(value: str, page: int) -> str:
        for code_point, count in invalid_xml_character_counts(value).items():
            audit["xml_sanitization_by_page"][page][code_point] += count
        return sanitize_xml_text(value)

    def visit(ref: str) -> None:
        obj = resolve_ref(document, ref)
        section = ref_section(ref)

        if section == "groups":
            for child in obj.get("children", []):
                visit(child["$ref"])
            return

        if section == "pictures":
            picture_provenance = obj.get("prov") or []
            if not picture_provenance:
                audit["unprovenanced_refs"].append(ref)
            for page in sorted({int(prov["page_no"]) for prov in picture_provenance}):
                pages[page].append({"type": "picture"})
                audit["picture_markers_by_page"][page] += 1

            def visit_picture_child(child_ref: str) -> None:
                child_obj = resolve_ref(document, child_ref)
                child_section = ref_section(child_ref)
                if child_section == "groups":
                    for descendant in child_obj.get("children", []):
                        visit_picture_child(descendant["$ref"])
                    return
                if child_section == "texts" and child_obj.get("label") in PICTURE_TEXT_LABELS:
                    audit["preserved_picture_text_by_label"][child_obj["label"]] += 1
                    visit(child_ref)
                    return
                for prov in child_obj.get("prov") or picture_provenance:
                    audit["ignored_picture_text_by_page"][int(prov["page_no"])] += 1

            for child in obj.get("children", []):
                visit_picture_child(child["$ref"])
            return

        if section == "texts":
            remove, reason = should_remove_text(obj)
            if remove:
                audit["removed_furniture"][reason] += 1
                return
            fragments = provenance_fragments(obj)
            if not fragments:
                audit["unprovenanced_refs"].append(ref)
                return
            for provenance_index, (page, fragment) in enumerate(fragments):
                if not fragment:
                    continue
                fragment = restore_list_marker(obj, fragment, provenance_index)
                fragment = sanitize_page_text(fragment, page)
                if not fragment:
                    continue
                pages[page].append(
                    {
                        "type": block_tag(obj.get("label")),
                        "text": fragment,
                    }
                )
            return

        if section == "tables":
            provenance = obj.get("prov") or []
            if not provenance:
                audit["unprovenanced_refs"].append(ref)
                return
            table_page = int(provenance[0]["page_no"])
            for cell in obj.get("data", {}).get("table_cells", []):
                sanitize_page_text(str(cell.get("text", "")), table_page)
            payload, conflicts = table_payload(obj)

            owned_refs = table_owned_text_refs(document, obj)
            duplicate_owned_refs = restored_table_text_refs.intersection(owned_refs)
            if duplicate_owned_refs:
                raise ValueError(
                    f"Table-owned text linked more than once: {sorted(duplicate_owned_refs)}"
                )
            restored_table_text_refs.update(owned_refs)
            owned_source_order = {owned_ref: index for index, owned_ref in enumerate(owned_refs)}
            ordered_items: list[tuple[str, str | None, dict[str, Any]]] = [
                ("table", None, obj)
            ]
            if owned_refs:
                ordered_items.extend(
                    ("text", owned_ref, resolve_ref(document, owned_ref))
                    for owned_ref in owned_refs
                )
                ordered_items.sort(
                    key=lambda item: layout_order_key(
                        item[2],
                        owned_source_order[item[1]] if item[1] is not None else len(owned_refs),
                    )
                )

            table_position = next(
                index for index, (item_type, _, _) in enumerate(ordered_items) if item_type == "table"
            )
            for item_index, (item_type, owned_ref, owned_obj) in enumerate(ordered_items):
                if item_type == "text":
                    label = str(owned_obj.get("label"))
                    audit["restored_table_text_by_label"][label] += 1
                    position = "before_table" if item_index < table_position else "after_table"
                    audit["restored_table_text_by_position"][position] += 1
                    visit(str(owned_ref))
                    continue

                page = table_page
                pages[page].append(
                    {
                        "type": "table",
                        "label": obj.get("label", "table"),
                        "payload": payload,
                        "catalog_text": (
                            table_catalog_text(obj)
                            if obj.get("label") != "document_index"
                            else None
                        ),
                    }
                )
            for conflict in conflicts:
                audit["table_conflicts"].append({"table_ref": ref, **conflict})
            return

        audit["unprovenanced_refs"].append(ref)

    for child in document.get("body", {}).get("children", []):
        visit(child["$ref"])

    audit["removed_furniture"] = dict(audit["removed_furniture"])
    audit["xml_sanitization_by_page"] = {
        page: dict(sorted(code_points.items()))
        for page, code_points in sorted(audit["xml_sanitization_by_page"].items())
    }
    audit["xml_sanitization_total"] = sum(
        sum(code_points.values())
        for code_points in audit["xml_sanitization_by_page"].values()
    )
    audit["ignored_picture_text_by_page"] = dict(audit["ignored_picture_text_by_page"])
    audit["picture_markers_by_page"] = dict(audit["picture_markers_by_page"])
    audit["preserved_picture_text_by_label"] = dict(audit["preserved_picture_text_by_label"])
    audit["restored_table_text_by_label"] = dict(audit["restored_table_text_by_label"])
    audit["restored_table_text_by_position"] = dict(audit["restored_table_text_by_position"])
    return pages, audit


def page_content_kind(blocks: list[dict[str, Any]]) -> str:
    """Return an internal content kind used only for empty-page handling/audits."""

    has_table = any(block["type"] == "table" for block in blocks)
    has_text = any(block["type"] != "table" and block.get("text", "").strip() for block in blocks)
    if has_table and has_text:
        return "text_and_table"
    if has_table:
        return "table"
    if has_text:
        return "text"
    return "empty"


def render_page_xml(blocks: list[dict[str, Any]]) -> str:
    root = ET.Element("page")
    for block in blocks:
        if block["type"] == "table":
            table_tag = "document_index" if block.get("label") == "document_index" else "table"
            render_table_xml(root, block["payload"], table_tag)
            continue
        if block["type"] == "picture":
            ET.SubElement(root, "picture")
            continue

        element = ET.SubElement(root, block["type"])
        element.text = block["text"]

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", short_empty_elements=True)


def render_page_plain_text(blocks: list[dict[str, Any]]) -> str:
    """Render corrected page content without XML markup or artificial headers."""

    parts: list[str] = []
    for block in blocks:
        if block["type"] == "picture":
            continue
        if block["type"] != "table":
            text = block.get("text", "").strip()
            if text:
                parts.append(text)
            continue

        rows = []
        for values in block["payload"].get("grid", []):
            rows.append(
                "\t".join("" if value is None else normalize_text(str(value)) for value in values).rstrip()
            )
        table_text = "\n".join(rows).strip()
        if table_text:
            parts.append(table_text)
    return "\n".join(parts)
