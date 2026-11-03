"""Document identity from filenames and reviewed fiscal dates from the catalog."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

FISCAL_DATE_CATALOG_PATH = Path(__file__).with_name("fiscal_date_catalog.json")


def load_fiscal_date_catalog() -> dict[str, str | None]:
    catalog = json.loads(FISCAL_DATE_CATALOG_PATH.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict):
        raise ValueError("fiscal_date_catalog.json must contain one JSON object")
    for document_name, fiscal_date in catalog.items():
        if not isinstance(document_name, str) or not document_name:
            raise ValueError("Fiscal-date catalog keys must be document names")
        if fiscal_date is not None:
            try:
                datetime.strptime(fiscal_date, "%Y-%m-%d")
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Invalid fiscal date for {document_name}: {fiscal_date!r}"
                ) from error
    return catalog


FISCAL_DATE_CATALOG = load_fiscal_date_catalog()


def filename_document_metadata(name: str) -> dict[str, Any]:
    """Return normalized identity and period labels encoded in a document name."""

    patterns = (
        (
            re.compile(r"^(?P<company>.+?)_(?P<year>\d{4})_10K$", re.IGNORECASE),
            "10k",
        ),
        (
            re.compile(
                r"^(?P<company>.+?)_(?P<year>\d{4})Q(?P<quarter>\d+)_10Q$",
                re.IGNORECASE,
            ),
            "10q",
        ),
        (
            re.compile(
                r"^(?P<company>.+?)_(?P<year>\d{4})_8K(?:_dated[-_](?P<date>\d{4}-\d{2}-\d{2}))?$",
                re.IGNORECASE,
            ),
            "8k",
        ),
        (
            re.compile(
                r"^(?P<company>.+?)_(?P<year>\d{4})Q(?P<quarter>\d+)_EARNINGS$",
                re.IGNORECASE,
            ),
            "earnings",
        ),
    )
    match: re.Match[str] | None = None
    document_type: str | None = None
    for pattern, candidate_type in patterns:
        match = pattern.match(name)
        if match:
            document_type = candidate_type
            break
    if match is None or document_type is None:
        raise ValueError(f"Unsupported document name: {name}")
    values = match.groupdict()
    return {
        "document_name": name,
        "company": values["company"].lower(),
        "fiscal_quarter": int(values["quarter"]) if values.get("quarter") else None,
        "fiscal_year": int(values["year"]),
        "document_type": document_type,
    }


def parse_document_metadata(name: str) -> dict[str, Any]:
    metadata = filename_document_metadata(name)
    if name not in FISCAL_DATE_CATALOG:
        raise ValueError(f"Fiscal-date catalog is missing document: {name}")
    metadata["fiscal_date"] = FISCAL_DATE_CATALOG[name]
    return metadata
