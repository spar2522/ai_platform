"""Shared parsing and extraction helpers for extractors."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from typing import Any


def parse_decimal(value: Any, default: Decimal | None = None) -> Decimal | None:
    """Safely convert strings or numbers to Decimal, handling commas, currencies, and whitespace.

    Handles:
    - Currency symbols (₹, $, €)
    - Parentheses for negative values (e.g., "(100.00)" → -100.00)
    - Trailing minus signs (e.g., "100.00-" → -100.00)
    - Commas as thousand separators
    """
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))

    s = str(value).strip()
    if not s or s.upper() in {"NA", "N/A", "NONE", "-"}:
        return default

    # Remove currency symbols, commas, and surrounding whitespace
    cleaned = re.sub(r"[₹$€\s]", "", s).replace(",", "")
    # Handle parentheses for negative values
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    # Handle trailing minus signs
    if cleaned.endswith("-"):
        cleaned = "-" + cleaned[:-1]

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return default


def normalize_text(text: Any) -> str:
    """Normalize string for robust anchor comparison.

    Normalization steps:
    1. Convert to string
    2. Collapse multiple whitespace characters to a single space
    3. Strip leading/trailing whitespace
    4. Convert to lowercase
    """
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def extract_counterparty_from_narration(narration: str) -> str | None:
    """Extract sensible counterparty business or individual name from Indian banking narrations.

    Supports formats:
    - UPI: UPI/<ref>/<name>/...
    - NEFT/RTGS: NEFT-<ref>-<name>-...
    - Cheque clearing: CLG/<name>/<bank>
    - Internal transfer: INF/.../trf /<name>

    Examples:
        UPI/ANKIT KUMA/aks007837-3@ok/... -> ANKIT KUMA
        NEFT-HDFCH00967227109-BHARAT PETROCHEMICALS LIMITED-... -> BHARAT PETROCHEMICALS LIMITED
        CLG/JOHN DOE/ABC BANK -> JOHN DOE
        INF/INTERNAL TRANSFER/trf /XYZ CORP -> XYZ CORP
    """
    # UPI format: UPI/<reference>/<name>/
    udi_match = re.match(r"^UPI/[^/]+/([^/]+)", narration)
    if udi_match:
        return udi_match.group(1)

    # NEFT/RTGS format: NEFT-<reference>-<name>-
    neft_match = re.match(r"^(NEFT|RTGS)-[^-]+-([^-\s]+)", narration)
    if neft_match:
        return neft_match.group(2)

    # Cheque clearing format: CLG/<name>/
    clg_match = re.match(r"^CLG/([^/]+)", narration)
    if clg_match:
        return clg_match.group(1)

    # Internal transfer format: .../trf /<name>
    inf_match = re.search(r"/trf\s*/([A-Za-z0-9_]+)", narration)
    if inf_match:
        return inf_match.group(1)

    return None