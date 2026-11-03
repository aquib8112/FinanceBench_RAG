"""Canonical table extraction, ordering, cataloguing, and XML rendering."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .docling import ref_section, ref_value, resolve_ref

TABLE_TEXT_LABELS = {"caption", "footnote"}

def table_owned_text_refs(document: dict[str, Any], table: dict[str, Any]) -> list[str]:
    """Return linked captions and footnotes in Docling's child order."""

    linked_refs = [
        ref_value(link)
        for field_name in ("captions", "footnotes")
        for link in table.get(field_name, [])
    ]
    linked_set = set(linked_refs)
    ordered_refs: list[str] = []
    seen: set[str] = set()
    for link in table.get("children", []):
        ref = ref_value(link)
        if ref in linked_set and ref not in seen:
            ordered_refs.append(ref)
            seen.add(ref)

    # Current Docling files include every linked caption and footnote in
    # `children`. Retain a deterministic fallback for a future file that only
    # supplies the role-specific reference list.
    for ref in linked_refs:
        if ref not in seen:
            ordered_refs.append(ref)
            seen.add(ref)

    for ref in ordered_refs:
        obj = resolve_ref(document, ref)
        if ref_section(ref) != "texts" or obj.get("label") not in TABLE_TEXT_LABELS:
            raise ValueError(f"Unexpected table-owned content {ref} on {table.get('self_ref')}")
    return ordered_refs


def layout_order_key(obj: dict[str, Any], source_order: int) -> tuple[int, float, int]:
    """Return a top-to-bottom page order key from Docling provenance."""

    provenance = obj.get("prov") or []
    if not provenance:
        raise ValueError(f"Cannot order unprovenanced element {obj.get('self_ref')}")
    first = provenance[0]
    bbox = first.get("bbox") or {}
    if "t" not in bbox:
        raise ValueError(f"Cannot order element without a top coordinate: {obj.get('self_ref')}")

    origin = bbox.get("coord_origin")
    if origin == "BOTTOMLEFT":
        vertical_position = -float(bbox["t"])
    elif origin == "TOPLEFT":
        vertical_position = float(bbox["t"])
    else:
        raise ValueError(f"Unknown coordinate origin {origin!r} on {obj.get('self_ref')}")
    return int(first["page_no"]), vertical_position, source_order


def table_payload(table: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cells = table.get("data", {}).get("table_cells", [])
    if not cells:
        return {"shape": {"rows": 0, "columns": 0}, "grid": [], "spans": []}, []

    row_count = max(int(cell["end_row_offset_idx"]) for cell in cells)
    column_count = max(int(cell["end_col_offset_idx"]) for cell in cells)
    grid: list[list[str | None]] = [["" for _ in range(column_count)] for _ in range(row_count)]
    owners: list[list[int | None]] = [[None for _ in range(column_count)] for _ in range(row_count)]
    spans: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []

    for cell_index, cell in enumerate(cells):
        row_start = int(cell["start_row_offset_idx"])
        row_end = int(cell["end_row_offset_idx"])
        column_start = int(cell["start_col_offset_idx"])
        column_end = int(cell["end_col_offset_idx"])
        value = cell.get("text", "").strip()

        occupied = []
        for row in range(row_start, row_end):
            for column in range(column_start, column_end):
                if owners[row][column] is not None:
                    occupied.append((row, column, owners[row][column]))
        if occupied:
            conflicts.append(
                {
                    "source_cell": cell_index,
                    "text": value,
                    "overlaps": [
                        {"at": [row, column], "existing_source_cell": owner}
                        for row, column, owner in occupied
                    ],
                }
            )

        # Preserve the first cell at every covered coordinate and report later
        # collisions. The anchor holds the value; merged coverage is explicit
        # null so it cannot be confused with a genuinely empty source cell.
        if not occupied:
            grid[row_start][column_start] = value
            for row in range(row_start, row_end):
                for column in range(column_start, column_end):
                    owners[row][column] = cell_index
                    if row != row_start or column != column_start:
                        grid[row][column] = None

        row_span = row_end - row_start
        column_span = column_end - column_start
        if row_span > 1 or column_span > 1:
            spans.append(
                {
                    "at": [row_start, column_start],
                    "row_span": row_span,
                    "column_span": column_span,
                }
            )

    payload: dict[str, Any] = {
        "shape": {"rows": row_count, "columns": column_count},
        "grid": grid,
        "spans": spans,
    }
    if conflicts:
        payload["conflicts"] = conflicts

    return payload, conflicts


def page_table_catalog(blocks: list[dict[str, Any]], page_id: str) -> list[dict[str, Any]]:
    """Return one compact catalogue record per ordinary table on a page."""

    result: list[dict[str, Any]] = []
    for block in blocks:
        if block["type"] != "table" or block.get("label") == "document_index":
            continue
        catalog_text = block.get("catalog_text")
        if not isinstance(catalog_text, dict):
            raise ValueError("Ordinary table is missing catalogue text")
        result.append(
            {
                "table_id": f"{page_id}:table:{len(result) + 1}",
                "column_headers": list(catalog_text["column_headers"]),
                "table_terms": list(catalog_text["table_terms"]),
            }
        )
    return result


def render_table_xml(parent: ET.Element, payload: dict[str, Any], tag: str = "table") -> None:
    """Render the canonical table grid as compact, pure XML."""

    table = ET.SubElement(parent, tag)
    spans = {
        tuple(span["at"]): (int(span["row_span"]), int(span["column_span"]))
        for span in payload.get("spans", [])
    }
    for row_index, values in enumerate(payload.get("grid", [])):
        row = ET.SubElement(table, "row")
        for column_index, value in enumerate(values):
            # A null is a position covered by an earlier rowspan/colspan cell.
            if value is None:
                continue
            attributes: dict[str, str] = {}
            row_span, column_span = spans.get((row_index, column_index), (1, 1))
            if row_span > 1:
                attributes["rowspan"] = str(row_span)
            if column_span > 1:
                attributes["colspan"] = str(column_span)
            cell = ET.SubElement(row, "cell", attributes)
            cell.text = value
