"""Shared parsing and extraction helpers for extractors."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from typing import Any


def parse_decimal(value: Any, default: Decimal | None = None) -> Decimal | None:
    """Safely convert strings or numbers to Decimal, handling commas, currencies, and whitespace."""
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))

    s = str(value).strip()
    if not s or s.upper() in {"NA", "N/A", "NONE", "-"}:
        return default

    # Remove commas, currency symbols (₹, $, €, INR), and surrounding quotes
    cleaned = re.sub(r"[₹$€\s]", "", s).replace(",", "")
    # Check for parentheses indicating negative: (100.00) -> -100.00
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    # Check for trailing minus: 100.00- -> -100.00 or 100.00 Cr / Dr
    if cleaned.endswith("-"):
        cleaned = "-" + cleaned[:-1]

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return default


def normalize_text(text: Any) -> str:
    """Normalize string for robust anchor comparison."""
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def extract_counterparty_from_narration(narration: str) -> str | None:
    """Extract sensible counterparty business or individual name from Indian banking narrations.

    Examples:
        UPI/ANKIT KUMA/aks007837-3@ok/... -> ANKIT KUMA
        NEFT-HDFCH00967227109-BHARAT PLY AND HARDWARE-... -> BHARAT PLY AND HARDWARE
        RTGS-PUNBR52026050116641857-BALAJEE HARDWARE-... -> BALAJEE HARDWARE
        CLG/UMA DEVI NARSARIA/UBI -> UMA DEVI NARSARIA
        INF/INFT/044247072221/trf /minupadia -> minupadia
    """
    if not narration:
        return None

    # UPI: UPI/<ref>/<name>/... or UPI/<name>/...
    upi_match = re.match(r"^UPI/(?:[0-9A-Za-z_-]+/)?([^/]+)", narration, re.IGNORECASE)
    if upi_match:
        cand = upi_match.group(1).strip()
        if cand and not cand.isdigit() and len(cand) > 2:
            return cand

    # NEFT / RTGS: NEFT-<ref>-<name>-...
    neft_match = re.match(r"^(?:NEFT|RTGS)-[A-Za-z0-9]+-([^-]+)", narration, re.IGNORECASE)
    if neft_match:
        cand = neft_match.group(1).strip()
        if cand and len(cand) > 2:
            return cand

    # Cheque clearing: CLG/<name>/<bank>
    clg_match = re.match(r"^CLG/([^/]+)", narration, re.IGNORECASE)
    if clg_match:
        cand = clg_match.group(1).strip()
        if cand and len(cand) > 2:
            return cand

    # Internal transfer: INF/.../trf /<name>
    inf_match = re.search(r"/trf\s*/([A-Za-z0-9_]+)", narration, re.IGNORECASE)
    if inf_match:
        cand = inf_match.group(1).strip()
        if cand and len(cand) > 2:
            return cand

    return None
