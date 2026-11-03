"""Docling references, provenance fragments, and page-continuation evidence."""

from __future__ import annotations

from typing import Any

def resolve_ref(document: dict[str, Any], ref: str) -> dict[str, Any]:
    obj: Any = document
    for part in ref.lstrip("#/").split("/"):
        obj = obj[int(part)] if part.isdigit() else obj[part]
    return obj


def ref_section(ref: str) -> str:
    return ref.lstrip("#/").split("/", 1)[0]


def ref_value(link: dict[str, Any]) -> str:
    """Return a Docling reference without coupling logic to its JSON key spelling."""

    if len(link) != 1:
        raise ValueError(f"Expected one reference value, found: {link}")
    return str(next(iter(link.values())))


def pages_for_ref(document: dict[str, Any], ref: str) -> list[int]:
    """Return provenance pages for an object and all of its descendants."""

    obj = resolve_ref(document, ref)
    pages = [int(prov["page_no"]) for prov in obj.get("prov") or []]
    for child in obj.get("children") or []:
        pages.extend(pages_for_ref(document, ref_value(child)))
    return pages


def derive_page_continuations(
    document: dict[str, Any],
) -> tuple[set[tuple[int, int]], dict[str, int]]:
    """Return adjacent page boundaries crossed by a Docling text or group.

    Output metadata intentionally collapses both source cases into one page-level
    navigation link. The audit keeps separate counts for debugging.
    """

    text_edges: set[tuple[int, int]] = set()
    group_edges: set[tuple[int, int]] = set()

    for obj in document.get("texts", []):
        pages = {int(prov["page_no"]) for prov in obj.get("prov") or []}
        for page in pages:
            if page + 1 in pages:
                text_edges.add((page, page + 1))

    for group in document.get("groups", []):
        child_pages = [
            pages_for_ref(document, ref_value(child))
            for child in group.get("children") or []
        ]
        for previous, current in zip(child_pages, child_pages[1:]):
            if not previous or not current:
                continue
            from_page = max(previous)
            to_page = min(current)
            if to_page == from_page + 1:
                group_edges.add((from_page, to_page))

    edges = text_edges | group_edges
    return edges, {
        "same_source_adjacent_boundaries": len(text_edges),
        "same_group_adjacent_boundaries": len(group_edges),
        "combined_adjacent_boundaries": len(edges),
    }


def provenance_fragments(obj: dict[str, Any]) -> list[tuple[int, str]]:
    """Return physical page numbers and their source text fragments."""

    text = obj.get("text", "")
    fragments = []
    for prov in obj.get("prov") or []:
        charspan = prov.get("charspan")
        if charspan and len(charspan) == 2:
            start, end = charspan
            fragment = text[start:end]
        else:
            fragment = text
        fragments.append((int(prov["page_no"]), fragment.strip()))
    return fragments


def should_remove_text(obj: dict[str, Any]) -> tuple[bool, str | None]:
    text = obj.get("text", "").strip()
    if text.lower() == "table of contents":
        return True, "table_of_contents_furniture"
    if obj.get("label") == "page_footer":
        return True, "page_footer"
    return False, None
