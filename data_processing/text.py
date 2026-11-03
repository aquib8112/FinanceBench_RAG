"""Text normalization, XML safety, table search text, and page UIDs."""

from __future__ import annotations

import hashlib
import unicodedata
from collections import defaultdict
from typing import Any, Iterable

UID_DIGEST_HEX_LENGTH = 16

def is_xml_10_character(character: str) -> bool:
    """Return whether one Unicode character is permitted in XML 1.0 text."""

    code_point = ord(character)
    return (
        code_point in {0x09, 0x0A, 0x0D}
        or 0x20 <= code_point <= 0xD7FF
        or 0xE000 <= code_point <= 0xFFFD
        or 0x10000 <= code_point <= 0x10FFFF
    )


def invalid_xml_character_counts(value: str) -> dict[str, int]:
    """Count XML-invalid characters by printable Unicode code-point label."""

    counts: dict[str, int] = defaultdict(int)
    for character in value:
        if not is_xml_10_character(character):
            counts[f"U+{ord(character):04X}"] += 1
    return dict(counts)


def sanitize_xml_text(value: str) -> str:
    """Remove characters forbidden from XML 1.0 text."""

    return "".join(character for character in value if is_xml_10_character(character))


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).replace("\r\n", "\n").replace("\r", "\n")
    value = sanitize_xml_text(value)
    return " ".join(value.split())


def deduplicate_texts(values: Iterable[str]) -> list[str]:
    """Normalize and case-insensitively deduplicate text while preserving order."""

    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = normalize_text("" if value is None else str(value))
        key = text.casefold()
        if text and key not in seen:
            result.append(text)
            seen.add(key)
    return result


def table_catalog_text(table: dict[str, Any]) -> dict[str, list[str]]:
    """Return compact searchable text without copying numerical table values.

    Docling-marked column headers remain separate. Body terms include explicit
    row roles and other cells containing alphabetic text, which retains useful
    categorical cells such as "Discount rate" even when Docling does not mark
    them as row labels.
    """

    ordered_cells = [
        cell
        for _, cell in sorted(
            enumerate(table.get("data", {}).get("table_cells", [])),
            key=lambda item: (
                int(item[1]["start_row_offset_idx"]),
                int(item[1]["start_col_offset_idx"]),
                int(item[1]["end_row_offset_idx"]),
                int(item[1]["end_col_offset_idx"]),
                item[0],
            ),
        )
    ]
    column_headers = deduplicate_texts(
        cell.get("text", "") for cell in ordered_cells if bool(cell.get("column_header"))
    )
    header_keys = {text.casefold() for text in column_headers}
    table_terms = deduplicate_texts(
        cell.get("text", "")
        for cell in ordered_cells
        if not bool(cell.get("column_header"))
        and (
            bool(cell.get("row_header"))
            or bool(cell.get("row_section"))
            or any(
                character.isalpha()
                for character in normalize_text(str(cell.get("text", "")))
            )
        )
    )
    table_terms = [text for text in table_terms if text.casefold() not in header_keys]
    return {"column_headers": column_headers, "table_terms": table_terms}


def page_uid(document_name: str, page_in_pdf: int, plain_text: str) -> str:
    """Return the page-scoped UID for the exact stored plain-text bytes."""

    digest = hashlib.sha256(plain_text.encode("utf-8")).hexdigest()[:UID_DIGEST_HEX_LENGTH]
    return f"{document_name.lower()}_{page_in_pdf}_{digest}"
