"""Build validated page chunks from Docling JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .metadata import FISCAL_DATE_CATALOG
from .pipeline import build_document
from .validation import validate_output

DEFAULT_DOCUMENTS = ("WALMART_2020_10K", "NETFLIX_2017_10K")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docling-dir", type=Path, required=True, help="Folder containing Docling JSON files")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--documents", nargs="+")
    selection.add_argument("--all-documents", action="store_true", help="build the complete fiscal-date catalog")
    parser.add_argument("--output", type=Path, required=True, help="Output chunk JSON file")
    parser.add_argument("--audit-output", type=Path, help="Defaults to OUTPUT with the suffix .audit.json")
    args = parser.parse_args()
    if args.audit_output is None:
        args.audit_output = args.output.with_suffix(".audit.json")
    return args


def main() -> None:
    args = parse_args()
    if args.output.resolve() == args.audit_output.resolve():
        raise ValueError("Chunk and audit output paths must differ")
    if args.all_documents:
        documents = list(FISCAL_DATE_CATALOG)
        source_names = {path.stem for path in args.docling_dir.glob("*.json")}
        catalog_names = set(documents)
        if source_names != catalog_names:
            raise ValueError(
                f"Source/catalog mismatch; missing={sorted(catalog_names - source_names)}, "
                f"extra={sorted(source_names - catalog_names)}"
            )
    else:
        documents = args.documents or list(DEFAULT_DOCUMENTS)

    chunks = []
    audits = []
    for document_name in documents:
        source_path = args.docling_dir / f"{document_name}.json"
        document = json.loads(source_path.read_text(encoding="utf-8"))
        if document["name"] != document_name:
            raise ValueError(f"Document name does not match its filename: {source_path}")
        document_chunks, audit = build_document(document)
        chunks.extend(document_chunks)
        audits.append(audit)
        print(f"{document_name}: {len(document_chunks)} chunks, {audit['omitted_page_count']} omitted pages", flush=True)

    validate_output(chunks, audits)
    for path, data in ((args.output, chunks), (args.audit_output, audits)):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        temporary.replace(path)
    print(f"Wrote {len(chunks)} chunks to {args.output}")
    print(f"Wrote construction audit to {args.audit_output}")
