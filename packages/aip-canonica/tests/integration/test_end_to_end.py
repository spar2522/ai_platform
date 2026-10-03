"""Integration tests for end-to-end conversion, validation, and graph construction."""

from decimal import Decimal
from pathlib import Path

from aip_canonica import BankStatement, Invoice, Ledger, understand


def test_end_to_end_real_icici_statement(icici_statement_path: Path):
    doc = understand(icici_statement_path, validate=True)
    assert isinstance(doc, BankStatement)
    assert len(doc.transactions) == 1518
    assert doc.opening_balance == Decimal("-15192804.00")
    assert doc.closing_balance == Decimal("-23519519.07")

    # Graph verification
    graph = doc.as_graph()
    assert graph.get_node(doc.id) is not None
    assert doc.account is not None
    assert len(graph.incoming(doc.account.id)) >= 1

    # Deterministic validation passed
    val = doc.validate()
    assert val.is_valid
    assert val.metrics["discrepancy"] == "0.00"


def test_end_to_end_standard_bank_statement_csv(standard_bank_statement_csv: Path):
    doc = understand(standard_bank_statement_csv, validate=True)
    assert isinstance(doc, BankStatement)
    assert len(doc.transactions) == 4
    assert doc.closing_balance == Decimal("64400.00")

    graph = doc.as_graph()
    assert graph.get_node(doc.id) is not None
    assert doc.account is not None
    assert len(graph.incoming(doc.account.id)) == 1

    val = doc.validate()
    assert val.is_valid


def test_different_layouts_produce_same_canonical_type(
    icici_statement_path: Path,
    standard_bank_statement_csv: Path,
):
    doc1 = understand(icici_statement_path)
    doc2 = understand(standard_bank_statement_csv)

    # Both map to the same BankStatement canonical domain type
    assert type(doc1) is BankStatement
    assert type(doc2) is BankStatement
    assert doc1.document_type == doc2.document_type


def test_end_to_end_invoice_csv(sample_invoice_csv: Path):
    doc = understand(sample_invoice_csv, validate=True)
    assert isinstance(doc, Invoice)
    assert doc.invoice_number == "INV-2026-0042"
    assert doc.total_amount == Decimal("92400.00")
    assert len(doc.lines) == 3

    graph = doc.as_graph()
    assert doc.issuer is not None
    assert len(graph.incoming(doc.issuer.id)) == 1


def test_end_to_end_invoice_excel(sample_invoice_xlsx: Path):
    doc = understand(sample_invoice_xlsx, validate=True)
    assert isinstance(doc, Invoice)
    assert doc.invoice_number == "INV-2026-0099"
    assert doc.total_amount == Decimal("17200.0")

    val = doc.validate()
    assert val.is_valid


def test_end_to_end_ledger_csv(sample_ledger_csv: Path):
    doc = understand(sample_ledger_csv, validate=True)
    assert isinstance(doc, Ledger)
    assert doc.closing_balance == Decimal("150000.00")
    assert len(doc.entries) == 3

    graph = doc.as_graph()
    assert doc.party is not None
    assert len(graph.incoming(doc.party.id)) == 1

    val = doc.validate()
    assert val.is_valid


def test_end_to_end_workflow_with_stateless_provenance(icici_statement_path: Path):
    """End-to-End Scenario: Ingestion with stateless source tracking.

    1. Client passes an ICICI Bank Statement file path.
    2. Canonica deterministically extracts 1,518 transactions with $0.00$ discrepancy.
    3. Validates balance math and constructs graph.
    4. Ensures child transactions link back to the exact source path without stateful side effects.
    """
    statement = understand(
        icici_statement_path,
        validate=True,
    )

    # Verify canonical extraction
    assert isinstance(statement, BankStatement)
    assert len(statement.transactions) == 1518
    assert statement.validate().is_valid

    # Verify document-level provenance points to the source path
    assert statement.provenance is not None
    assert statement.provenance.source == str(icici_statement_path)

    # Verify granular entity-level provenance
    first_txn = statement.transactions[0]
    assert first_txn.provenance is not None
    assert first_txn.provenance.source == str(icici_statement_path)
    assert first_txn.provenance.row == 18


def test_end_to_end_workflow_ai_learning_discovery_lifecycle(sample_invoice_csv: Path, tmp_path: Path):
    """End-to-End Scenario: AI Strategy Learner discovers layout & synthesizes code.

    1. Ingest an unfamiliar document with learning_mode=True.
    2. AI StrategyLearner analyzes structural anchors, table headers, and metadata.
    3. Discovers richer metadata and generates candidate extractor code on disk.
    4. Generates comprehensive markdown report with clickable file links.
    """
    from unittest.mock import AsyncMock
    from aip_provider.models import AIResponse

    mock_ai = AsyncMock()
    mock_ai.generate.return_value = AIResponse(
        text="""```json
{
    "name": "enterprise_gst_invoice",
    "document_type": "invoice",
    "anchor_keywords": ["tax invoice", "gstin"],
    "table_header_keywords": ["item", "qty", "rate", "taxable_value", "cgst", "sgst"],
    "column_mapping": {"description": "Item", "amount": "Taxable Value"},
    "metadata_fields": {
        "seller_gstin": "Seller GSTIN",
        "buyer_gstin": "Buyer GSTIN",
        "place_of_supply": "Place of Supply",
        "reverse_charge": "Reverse Charge"
    },
    "notes": "Compliant Indian GST B2B tax invoice"
}
```""",
        model="mock-gemini",
    )

    doc = understand(
        sample_invoice_csv,
        learning_mode=True,
        ai=mock_ai,
    )

    assert isinstance(doc, Invoice)
    assert doc.validate().is_valid

    # Verify that StrategyLearner wrote extractor and report to disk
    gen_dir = Path.cwd() / ".canonica" / "generated"
    extractor_file = gen_dir / "enterprise_gst_invoice_extractor.py"
    report_file = gen_dir / "enterprise_gst_invoice_report.md"

    assert extractor_file.exists()
    assert report_file.exists()

    # The generated Python file is valid syntax defining the new extractor
    code = extractor_file.read_text(encoding="utf-8")
    assert "class EnterpriseGstInvoiceExtractor:" in code
    assert 'return "enterprise_gst_invoice"' in code

    # The report contains the full markdown documentation
    report_content = report_file.read_text(encoding="utf-8")
    assert "# Canonica AI Strategy Learning Report" in report_content
    assert "seller_gstin" in report_content


def test_end_to_end_pdf_statement_option_a_deterministic(tmp_path: Path):
    """End-to-End: Native digital PDF parsed deterministically into BankStatement without AI."""
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    pdf_file = tmp_path / "corporate_statement.pdf"
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    content = (
        b"BT /F1 12 Tf 72 700 Td "
        b"(Account No: 123456789) Tj 0 -20 Td "
        b"(Opening Balance: 50000.00) Tj 0 -20 Td "
        b"(Date\tDescription\tWithdrawal\tDeposit\tBalance) Tj 0 -20 Td "
        b"(2024-01-05\tOffice Rent Payment\t15000.00\t0.00\t35000.00) Tj 0 -20 Td "
        b"(2024-01-10\tClient Inflow\t0.00\t25000.00\t60000.00) Tj "
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

    with open(pdf_file, "wb") as f:
        writer.write(f)

    # Ingest through top-level understand()
    doc = understand(pdf_file, validate=True)
    assert isinstance(doc, BankStatement)
    assert len(doc.transactions) == 2
    assert doc.opening_balance == Decimal("50000.00")
    assert doc.closing_balance == Decimal("60000.00")

    # Reconciliation and graph construction
    val = doc.validate()
    assert val.is_valid
    assert val.metrics.get("discrepancy") == "0.00"
    graph = doc.as_graph()
    assert len(graph.nodes) >= 3


def test_end_to_end_pdf_statement_option_b_fallback(tmp_path: Path, caplog):
    """End-to-End: Scanned/image PDF triggers Option B AI OCR fallback with highlighted banners."""
    import logging
    from unittest.mock import AsyncMock
    from aip_provider.models import AIResponse
    from pypdf import PdfWriter

    pdf_file = tmp_path / "scanned_invoice.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with open(pdf_file, "wb") as f:
        writer.write(f)

    mock_ai = AsyncMock()
    mock_ai.generate.return_value = AIResponse(
        text="""```json
{
    "sheets": [
        {
            "name": "Page 1",
            "rows": [
                ["Invoice Number", "INV-2026-9999"],
                ["Issue Date", "2026-03-01"],
                ["Due Date", "2026-03-31"],
                ["Issuer Name", "Enterprise Cloud Services"],
                ["Item Description", "Quantity", "Unit Price", "Amount"],
                ["Cloud Server Hosting", "1", "1000.00", "1000.00"],
                ["Subtotal", "1000.00"],
                ["Total", "1000.00"]
            ]
        }
    ]
}
```""",
        model="mock-gemini",
    )

    with caplog.at_level(logging.INFO):
        doc = understand(pdf_file, ai=mock_ai, validate=True)

    assert isinstance(doc, Invoice)
    assert doc.invoice_number == "INV-2026-9999"
    assert doc.total_amount == Decimal("1000.00")
    assert doc.validate().is_valid

    # Demarcation banner logged
    assert "[Canonica][AI Fallback]" in caplog.text
    assert "============================================================" in caplog.text


def test_end_to_end_pdf_triggers_ai_when_calculation_does_not_match(tmp_path: Path, caplog):
    """When a digital PDF (>50 chars, >3 rows) fails financial calculation/reconciliation,
    Canonica automatically switches from Option A to Option B (AI Fallback) to repair table structure.
    """
    import logging
    from unittest.mock import AsyncMock
    from aip_provider.models import AIResponse
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    pdf_file = tmp_path / "mismatched_statement.pdf"
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    # Option A text has a calculation mismatch: Opening 50000 - 15000 != Closing 30000 (discrepancy of 5000.00)
    content = (
        b"BT /F1 12 Tf 72 700 Td "
        b"(Account No: 987654321) Tj 0 -20 Td "
        b"(Opening Balance: 50000.00) Tj 0 -20 Td "
        b"(Date\tDescription\tWithdrawal\tDeposit\tBalance) Tj 0 -20 Td "
        b"(2024-01-05\tOffice Rent\t15000.00\t0.00\t30000.00) Tj "
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

    with open(pdf_file, "wb") as f:
        writer.write(f)

    # AI Fallback repairs the missing transaction that caused the discrepancy
    mock_ai = AsyncMock()
    mock_ai.generate.return_value = AIResponse(
        text="""```json
{
    "sheets": [
        {
            "name": "Page 1",
            "rows": [
                ["Account No:", "987654321"],
                ["Opening Balance:", "50000.00"],
                ["Date", "Description", "Withdrawal", "Deposit", "Balance"],
                ["2024-01-05", "Office Rent", "15000.00", "0.00", "35000.00"],
                ["2024-01-08", "Equipment Purchase", "5000.00", "0.00", "30000.00"],
                ["Closing Balance:", "30000.00"]
            ]
        }
    ]
}
```""",
        model="mock-gemini",
    )

    with caplog.at_level(logging.INFO):
        doc = understand(pdf_file, ai=mock_ai, validate=True)

    assert isinstance(doc, BankStatement)
    assert len(doc.transactions) == 2
    assert doc.opening_balance == Decimal("50000.00")
    assert doc.closing_balance == Decimal("30000.00")
    assert doc.validate().is_valid

    # Verify AI fallback was engaged due to calculation mismatch
    assert "[Canonica][AI Fallback]" in caplog.text
    assert "calculation" in caplog.text or "discrepancy" in caplog.text


def test_end_to_end_pdf_triggers_ai_when_document_type_unidentified(tmp_path: Path, caplog):
    """When a digital PDF (>50 chars, >3 rows) cannot be identified as any known document type,
    Canonica switches to Option B (AI Fallback) to discover layout structure.
    """
    import logging
    from unittest.mock import AsyncMock
    from aip_provider.models import AIResponse
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    pdf_file = tmp_path / "jumbled_unknown.pdf"
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    # Text contains plenty of characters (>50 chars, >3 rows) but no recognizable financial headers
    content = (
        b"BT /F1 12 Tf 72 700 Td "
        b"(Alpha    Beta    Gamma    Delta    Epsilon) Tj "
        b"0 -20 Td (100    200    300    400    500) Tj "
        b"0 -20 Td (600    700    800    900    1000) Tj "
        b"0 -20 Td (1100    1200    1300    1400    1500) Tj "
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

    with open(pdf_file, "wb") as f:
        writer.write(f)

    # AI identifies the true financial table and normalizes headers
    mock_ai = AsyncMock()
    mock_ai.generate.return_value = AIResponse(
        text="""```json
{
    "sheets": [
        {
            "name": "Page 1",
            "rows": [
                ["Account Number:", "ACC-112233"],
                ["Opening Balance:", "1000.00"],
                ["Date", "Description", "Withdrawal", "Deposit", "Balance"],
                ["2024-02-01", "Utility Payment", "200.00", "0.00", "800.00"],
                ["2024-02-05", "Direct Deposit", "0.00", "500.00", "1300.00"]
            ]
        }
    ]
}
```""",
        model="mock-gemini",
    )

    with caplog.at_level(logging.INFO):
        doc = understand(pdf_file, ai=mock_ai, validate=True)

    assert isinstance(doc, BankStatement)
    assert len(doc.transactions) == 2
    assert doc.closing_balance == Decimal("1300.00")
    assert doc.validate().is_valid

    # Verify AI fallback was triggered due to unidentified document type
    assert "[Canonica][AI Fallback]" in caplog.text
    assert "Could not identify document type" in caplog.text
