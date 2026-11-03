"""FinanceBench document-to-page chunk processing package."""

from .pipeline import build_document
from .validation import validate_output

__all__ = ["build_document", "validate_output"]
