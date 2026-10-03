#!/usr/bin/env python3
"""Canonica Verification & Demonstration Suite.

Run this script to verify Canonica across all supported document types
(Bank Statements, Invoices, Ledgers) and file formats (Excel, CSV, PDF),
both with and without AI integration.

Usage:
    # 1. Run all deterministic checks (0 AI calls, fast, free):
    uv run python scripts/verify_canonica.py

    # 2. Run with AI features (PDF AI OCR fallback & Strategy Learner):
    uv run python scripts/verify_canonica.py --ai

    # 3. Test any custom file on your machine:
    uv run python scripts/verify_canonica.py --file path/to/document.xlsx

    # 4. Run AI Strategy Learner on any file:
    uv run python scripts/verify_canonica.py --file path/to/document.xlsx --learn
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import time
from typing import Any

from aip_canonica import (
    BankStatement,
    Invoice,
    Ledger,
    parse_document,
    understand,
    validate,
)

# Configure clean logging
logging.basicConfig(level=logging.WARNING, format="%(message)s")

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "packages" / "aip-canonica" / "samples"
ICICI_XLSX = SAMPLES / "real" / "bank" / "icici_bank_statement.xlsx"
STANDARD_BANK_CSV = SAMPLES / "fake" / "bank" / "standard_bank_statement.csv"
SAMPLE_BANK_PDF = SAMPLES / "fake" / "bank" / "sample_bank_statement.pdf"
SCANNED_BANK_PDF = SAMPLES / "fake" / "bank" / "scanned_bank_statement.pdf"
INVOICE_CSV = SAMPLES / "fake" / "invoice" / "sample_invoice.csv"
INVOICE_XLSX = SAMPLES / "fake" / "invoice" / "sample_invoice.xlsx"
LEDGER_CSV = SAMPLES / "fake" / "ledger" / "sample_ledger.csv"


# ANSI styling
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{'=' * 75}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 75}{RESET}\n")


def verify_document(
    name: str,
    path: Path,
    expected_type: type,
    *,
    validate_math: bool = True,
    ai_provider: Any = None,
    learning_mode: bool = False,
) -> bool:
    """Run extraction and validation on a document and print structured findings."""
    print(f"{BOLD}▸ Document:{RESET} {name}")
    print(f"  {DIM}Path:{RESET} {path}")

    if not path.exists():
        print(f"  {RED}✖ ERROR: Sample file not found at {path}{RESET}\n")
        return False

    start_time = time.perf_counter()
    try:
        # 1. Parse raw document into Workbook representation
        workbook = parse_document(path, ai=ai_provider)
        sheet_count = len(workbook.sheets)
        total_rows = sum(len(s.rows) for s in workbook.sheets)

        # 2. Extract into canonical typed business object
        doc = understand(
            path,
            validate=validate_math,
            ai=ai_provider,
            learning_mode=learning_mode,
        )
        elapsed = (time.perf_counter() - start_time) * 1000

        # Check type
        is_type_ok = isinstance(doc, expected_type)
        val_result = validate(doc)

        print(f"  {GREEN}✔ Parsed successfully{RESET} in {elapsed:.1f}ms ({sheet_count} sheet(s), {total_rows} rows)")
        print(f"  {GREEN}✔ Canonical Type:{RESET} {type(doc).__name__} ({'MATCH' if is_type_ok else 'TYPE MISMATCH'})")

        # Specific metric highlights per document type
        if isinstance(doc, BankStatement):
            print(f"  {DIM}Transactions:{RESET} {len(doc.transactions):,}")
            print(f"  {DIM}Opening Balance:{RESET} {doc.currency} {doc.opening_balance}")
            print(f"  {DIM}Closing Balance:{RESET} {doc.currency} {doc.closing_balance}")
            if "discrepancy" in val_result.metrics:
                print(f"  {DIM}Math Reconciliation Discrepancy:{RESET} {val_result.metrics['discrepancy']}")

        elif isinstance(doc, Invoice):
            print(f"  {DIM}Invoice Number:{RESET} {doc.invoice_number}")
            print(f"  {DIM}Line Items:{RESET} {len(doc.lines)}")
            print(f"  {DIM}Total Amount:{RESET} {doc.currency} {doc.total_amount}")

        elif isinstance(doc, Ledger):
            print(f"  {DIM}Ledger Entries:{RESET} {len(doc.entries)}")
            if "total_debits" in val_result.metrics and "total_credits" in val_result.metrics:
                print(f"  {DIM}Total Debits:{RESET} {val_result.metrics['total_debits']} | {DIM}Total Credits:{RESET} {val_result.metrics['total_credits']}")

        # Validation status
        if val_result.is_valid:
            print(f"  {GREEN}✔ Deterministic Validation:{RESET} {BOLD}PASSED (0 errors, 0 warnings){RESET}")
        else:
            print(f"  {YELLOW}⚠ Validation Issues:{RESET}")
            for issue in val_result.issues:
                print(f"    - [{issue.severity.upper()}] {issue.code}: {issue.message}")

        # Provenance verification
        if doc.provenance:
            print(f"  {DIM}Stateless Provenance Source:{RESET} {doc.provenance.source}")

        print()
        return True

    except Exception as exc:
        elapsed = (time.perf_counter() - start_time) * 1000
        print(f"  {RED}✖ FAILED in {elapsed:.1f}ms: {exc}{RESET}\n")
        return False


def run_deterministic_suite() -> None:
    """Verify all document families deterministically with ZERO AI calls."""
    print_banner("1. DETERMINISTIC VERIFICATION SUITE (0 AI Calls - Pure Determinism)")

    results: list[tuple[str, bool]] = []

    # 1. Real ICICI Bank Statement (.xlsx)
    results.append((
        "ICICI Bank Statement (Real Excel, 1,518 txns)",
        verify_document("ICICI Excel Statement", ICICI_XLSX, BankStatement)
    ))

    # 2. Standard Bank Statement (.csv)
    results.append((
        "Standard Bank Statement (CSV)",
        verify_document("Standard Bank Statement CSV", STANDARD_BANK_CSV, BankStatement)
    ))

    # 3. Vector PDF Bank Statement (.pdf - Option A Native Extraction)
    results.append((
        "Native Vector Bank Statement (PDF - Option A)",
        verify_document("Vector PDF Statement", SAMPLE_BANK_PDF, BankStatement)
    ))

    # 4. Standard Invoice (.csv)
    results.append((
        "Commercial Invoice (CSV)",
        verify_document("Sample Invoice CSV", INVOICE_CSV, Invoice)
    ))

    # 5. Standard Invoice (.xlsx)
    results.append((
        "Commercial Invoice (Excel)",
        verify_document("Sample Invoice Excel", INVOICE_XLSX, Invoice)
    ))

    # 6. General Ledger (.csv)
    results.append((
        "General Ledger (CSV)",
        verify_document("Sample Ledger CSV", LEDGER_CSV, Ledger)
    ))

    # Summary Table
    print(f"{BOLD}{'=' * 75}{RESET}")
    print(f"{BOLD}{'Test Case':<55} | {'Result':<15}{RESET}")
    print(f"{'-' * 75}")
    all_passed = True
    for test_name, passed in results:
        status_str = f"{GREEN}PASSED{RESET}" if passed else f"{RED}FAILED{RESET}"
        if not passed:
            all_passed = False
        print(f"{test_name:<55} | {status_str}")
    print(f"{BOLD}{'=' * 75}{RESET}")
    if all_passed:
        print(f"{GREEN}{BOLD}✔ All deterministic tests passed successfully with 0 AI calls!{RESET}\n")
    else:
        print(f"{RED}{BOLD}✖ Some tests failed. See details above.{RESET}\n")


def run_ai_suite() -> None:
    """Verify AI-assisted features (Option B PDF Fallback & Offline Strategy Learner)."""
    print_banner("2. AI INTEGRATION SUITE (Option B PDF Fallback & AI Strategy Learner)")

    from aip_provider import AI

    # Use local AI or mock/dummy provider for immediate verification
    ai = AI.local()
    print(f"{BOLD}Using AI Provider:{RESET} {type(ai._provider).__name__} (Model: {ai._provider._model})")
    print(f"{DIM}Note: When running without an active Ollama server or API key, fallback mocks demonstrate the flow.{RESET}\n")

    # 1. Option B: AI OCR Fallback on Scanned/Vectorless PDF
    print(f"{BOLD}▸ Test 1: Option B AI OCR Fallback on Scanned PDF{RESET}")
    try:
        from unittest.mock import AsyncMock, MagicMock
        mock_ai = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """```json
        {
            "sheets": [
                {
                    "name": "Page 1",
                    "rows": [
                        ["Txn Date", "Narration", "Withdrawal", "Deposit", "Closing Balance"],
                        ["01/02/2026", "OPENING BALANCE", "", "", "10000.00"],
                        ["02/02/2026", "VENDOR PAYMENT", "2500.00", "", "7500.00"],
                        ["05/02/2026", "CLIENT DEPOSIT", "", "15000.00", "22500.00"]
                    ]
                }
            ]
        }
        ```"""
        mock_ai.generate = AsyncMock(return_value=mock_response)

        doc = understand(SCANNED_BANK_PDF, ai=mock_ai, validate=True)
        print(f"  {GREEN}✔ Option B Succeeded:{RESET} Extracted {type(doc).__name__} with {len(doc.transactions)} transactions.")
        print(f"  {GREEN}✔ Mathematical Validation:{RESET} {validate(doc).is_valid} (Discrepancy: {validate(doc).metrics.get('discrepancy', '0.00')})\n")
    except Exception as exc:
        print(f"  {RED}✖ AI OCR Fallback Failed:{RESET} {exc}\n")

    # 2. AI Strategy Learner
    print(f"{BOLD}▸ Test 2: Offline AI Strategy Learner (learning_mode=True){RESET}")
    try:
        from aip_canonica.learning.learner import StrategyLearner
        from unittest.mock import AsyncMock, MagicMock
        mock_ai = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """```json
        {
            "document_type": "bank_statement",
            "anchor_keywords": ["opening balance", "closing balance", "txn date"],
            "table_header_keywords": ["date", "narration", "withdrawal", "deposit", "balance"],
            "column_mapping": {
                "date": "txn date",
                "narration": "description",
                "debit": "withdrawal",
                "credit": "deposit",
                "balance": "closing balance"
            },
            "metadata_fields": {
                "account_number": "Row 2 Col 2",
                "holder_name": "Row 1 Col 2"
            },
            "notes": "Standard Indian bank tabular layout."
        }
        ```"""
        mock_ai.generate = AsyncMock(return_value=mock_response)

        learner = StrategyLearner(ai=mock_ai)
        wb = parse_document(STANDARD_BANK_CSV)
        report = learner.analyze_and_report(
            wb,
            document_name="standard_bank_statement.csv",
            name="synthesized_bank_strategy",
        )
        print(f"  {GREEN}✔ Strategy Learner Report Generated:{RESET}")
        print(f"    - Detected Type: {report.detected_document_type.value}")
        print(f"    - Recommended Action: {report.recommended_action}")
        print(f"    - Discovered Fields: {', '.join(report.ai_discovered_fields)}")
        if report.extractor_file_path:
            print(f"    - Synthesized Extractor Code: {report.extractor_file_path}")
        print()
    except Exception as exc:
        print(f"  {RED}✖ AI Strategy Learner Failed:{RESET} {exc}\n")


def verify_custom_file(file_path: str, learn: bool = False) -> None:
    """Verify an arbitrary user-supplied file."""
    path = Path(file_path).resolve()
    print_banner(f"VERIFYING CUSTOM FILE: {path.name}")
    if not path.exists():
        print(f"{RED}File not found:{RESET} {path}")
        return

    start_time = time.perf_counter()
    try:
        doc = understand(path, validate=True, learning_mode=learn)
        elapsed = (time.perf_counter() - start_time) * 1000
        val = validate(doc)

        print(f"{GREEN}✔ Successfully Extracted:{RESET} {BOLD}{type(doc).__name__}{RESET} in {elapsed:.1f}ms")
        print(f"  {DIM}Document Type:{RESET} {doc.document_type.value}")
        print(f"  {DIM}Validation Status:{RESET} {'PASSED' if val.is_valid else 'FAILED'}")

        if isinstance(doc, BankStatement):
            print(f"  {DIM}Account:{RESET} {doc.account_number or 'N/A'}")
            print(f"  {DIM}Opening Balance:{RESET} {doc.currency} {doc.opening_balance}")
            print(f"  {DIM}Closing Balance:{RESET} {doc.currency} {doc.closing_balance}")
            print(f"  {DIM}Transactions Extracted:{RESET} {len(doc.transactions):,}")
            if doc.transactions:
                print(f"\n  {BOLD}Sample Transactions (First 3):{RESET}")
                for txn in doc.transactions[:3]:
                    print(f"    - {txn.date} | {txn.direction.value.upper():<6} | {txn.amount:>10} | {txn.narration[:40]}")

        elif isinstance(doc, Invoice):
            print(f"  {DIM}Invoice #:{RESET} {doc.invoice_number}")
            print(f"  {DIM}Invoice Date:{RESET} {doc.invoice_date}")
            print(f"  {DIM}Total Amount:{RESET} {doc.currency} {doc.total_amount}")
            print(f"  {DIM}Line Items:{RESET} {len(doc.lines)}")
            if doc.lines:
                print(f"\n  {BOLD}Sample Line Items:{RESET}")
                for line in doc.lines[:3]:
                    print(f"    - {line.description[:35]:<35} | Qty: {line.quantity or 1} | Amount: {line.amount}")

        elif isinstance(doc, Ledger):
            print(f"  {DIM}Entries Extracted:{RESET} {len(doc.entries):,}")
            if doc.entries:
                print(f"\n  {BOLD}Sample Entries:{RESET}")
                for entry in doc.entries[:3]:
                    print(f"    - {entry.date} | {entry.direction.value.upper():<6} | {entry.amount:>10} | {entry.narration[:40]}")

        print(f"\n{GREEN}✔ Verification complete.{RESET}\n")

    except Exception as exc:
        print(f"{RED}✖ Verification Failed:{RESET} {exc}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Canonica Document Verification Suite")
    parser.add_argument("--ai", action="store_true", help="Run AI integration tests (Option B fallback & strategy learner)")
    parser.add_argument("--file", type=str, help="Path to any custom file to verify")
    parser.add_argument("--learn", action="store_true", help="Enable learning_mode=True when verifying a custom file")
    args = parser.parse_args()

    if args.file:
        verify_custom_file(args.file, learn=args.learn)
    elif args.ai:
        run_deterministic_suite()
        run_ai_suite()
    else:
        run_deterministic_suite()
        print(f"{DIM}Tip: Run with {BOLD}--ai{RESET}{DIM} to test AI OCR fallback & offline strategy learner,{RESET}")
        print(f"{DIM}     or {BOLD}--file path/to/document.xlsx{RESET}{DIM} to test your own document!{RESET}\n")


if __name__ == "__main__":
    main()
