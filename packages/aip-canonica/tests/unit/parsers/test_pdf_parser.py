"""Unit tests for PdfParser covering Option A deterministic parsing and Option B AI fallback."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from aip_canonica.parsers.pdf_parser import PdfParser


def _create_sample_vector_pdf(target_path: Path) -> Path:
    """Helper to create a genuine vector PDF with embedded text stream using pypdf."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    content = (
        b"BT /F1 12 Tf 72 700 Td "
        b"(Date    Description    Debit    Credit    Balance) Tj "
        b"0 -20 Td (2023-01-01    Opening Balance        10000.00) Tj "
        b"0 -20 Td (2023-01-02    Vendor Payment    500.00        9500.00) Tj "
        b"0 -20 Td (2023-01-03    Client Credit        1500.00    11000.00) Tj "
        b"ET"
    )
    stream = DecodedStreamObject()
    stream.set_data(content)
    page[NameObject("/Contents")] = stream

    font_dict = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_dict}),
        }
    )

    with open(target_path, "wb") as f:
        writer.write(f)

    return target_path


def _create_empty_or_scanned_pdf(target_path: Path) -> Path:
    """Helper to create a PDF with 0 extractable text (simulating raster scan or blank page)."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with open(target_path, "wb") as f:
        writer.write(f)
    return target_path


def test_option_a_deterministic_parsing_succeeds(tmp_path: Path):
    """Option A parses vector PDF deterministically without invoking any AI."""
    pdf_file = _create_sample_vector_pdf(tmp_path / "statement.pdf")

    mock_ai = MagicMock()
    parser = PdfParser(ai=mock_ai, min_chars=30, min_rows=3)
    workbook = parser.parse(pdf_file)

    assert len(workbook.sheets) == 1
    sheet = workbook.sheets[0]
    assert sheet.name == "Page_1"
    assert len(sheet.rows) >= 4

    # Verify header row
    header_vals = [c.value for c in sheet.rows[0].cells]
    assert "Date" in header_vals
    assert "Description" in header_vals
    assert "Balance" in header_vals

    # Verify transaction rows
    first_tx = [c.value for c in sheet.rows[1].cells]
    assert "2023-01-01" in first_tx
    assert "Opening Balance" in first_tx

    # Check cell locations
    assert sheet.rows[0].cells[0].location.address == "A1"
    assert sheet.rows[0].cells[0].location.sheet == "Page_1"

    # CRITICAL: Verify AI was never called!
    mock_ai.generate.assert_not_called()


def test_option_a_fails_quality_check_and_engages_option_b_ai_fallback(
    tmp_path: Path, caplog
):
    """When PDF has insufficient text (e.g. scanned image), triggers Option B AI fallback with divider banners."""
    scanned_pdf = _create_empty_or_scanned_pdf(tmp_path / "scanned_doc.pdf")

    # Set up AI mock returning structured table grid
    mock_ai = MagicMock()
    mock_response = MagicMock()
    mock_response.text = """```json
    {
        "sheets": [
            {
                "name": "Page 1",
                "rows": [
                    ["Txn Date", "Narration", "Withdrawal", "Deposit", "Closing Balance"],
                    ["15/01/2024", "ATM CASH WITHDRAWAL", "2000.00", "", "48000.00"],
                    ["16/01/2024", "SALARY CREDIT", "", "85000.00", "133000.00"]
                ]
            }
        ]
    }
    ```"""
    mock_ai.generate = AsyncMock(return_value=mock_response)

    parser = PdfParser(ai=mock_ai, min_chars=50, min_rows=3)

    import logging

    with caplog.at_level(logging.INFO):
        workbook = parser.parse(scanned_pdf)

    # Verify Option B fallback took effect
    assert len(workbook.sheets) == 1
    sheet = workbook.sheets[0]
    assert sheet.name == "Page 1"
    assert len(sheet.rows) == 3

    assert [c.value for c in sheet.rows[0].cells] == [
        "Txn Date",
        "Narration",
        "Withdrawal",
        "Deposit",
        "Closing Balance",
    ]
    assert sheet.rows[1].cells[0].value == "15/01/2024"
    assert sheet.rows[1].cells[1].value == "ATM CASH WITHDRAWAL"
    assert sheet.rows[1].cells[2].value == "2000.00"

    # Verify AI was called
    mock_ai.generate.assert_called_once()

    # Verify visual demarcation banner was logged
    log_output = caplog.text
    assert "============================================================" in log_output
    assert "[Canonica][AI Fallback]" in log_output
    assert "scanned_doc.pdf" in log_output


def test_scanned_pdf_fails_when_ai_cannot_reconstruct(tmp_path: Path):
    """When Option A fails and Option B AI cannot parse rows, raises ValueError."""
    scanned_pdf = _create_empty_or_scanned_pdf(tmp_path / "empty.pdf")

    mock_ai = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Sorry, I could not extract any tables."
    mock_ai.generate = AsyncMock(return_value=mock_response)

    parser = PdfParser(ai=mock_ai, min_chars=50, min_rows=3)

    with pytest.raises(ValueError, match="Failed to parse PDF document"):
        parser.parse(scanned_pdf)


def test_public_parse_document_handles_pdf(tmp_path: Path):
    """End-to-end integration via top-level parse_document API."""
    from aip_canonica.api import parse_document

    pdf_file = _create_sample_vector_pdf(tmp_path / "test.pdf")
    workbook = parse_document(pdf_file)

    assert len(workbook.sheets) == 1
    assert len(workbook.sheets[0].rows) >= 4
