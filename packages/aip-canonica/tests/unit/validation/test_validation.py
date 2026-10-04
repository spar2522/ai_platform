"""Unit tests for deterministic validation rules."""

from decimal import Decimal

from aip_canonica.models.bank_statement import BankStatement, Transaction
from aip_canonica.models.base import TransactionDirection
from aip_canonica.models.invoice import Invoice, InvoiceLine, Tax
from aip_canonica.models.ledger import EntryDirection, Ledger, LedgerEntry
from aip_canonica.validation.validator import (
    BankStatementValidator,
    InvoiceValidator,
    LedgerValidator,
    validate,
)


def test_bank_statement_validation_success():
    stmt = BankStatement(
        id="s1",
        opening_balance=Decimal("1000.00"),
        closing_balance=Decimal("1200.00"),
        transactions=[
            Transaction(id="t1", date="2026-01-01", amount=Decimal("300.00"), direction=TransactionDirection.CREDIT, narration="In"),
            Transaction(id="t2", date="2026-01-02", amount=Decimal("100.00"), direction=TransactionDirection.DEBIT, narration="Out"),
        ],
    )
    result = BankStatementValidator().validate(stmt)
    assert result.is_valid
    assert len(result.errors) == 0
    assert result.metrics["discrepancy"] == "0.00"


def test_bank_statement_validation_failure():
    stmt = BankStatement(
        id="s1",
        opening_balance=Decimal("1000.00"),
        closing_balance=Decimal("9999.00"),  # Mismatch!
        transactions=[
            Transaction(id="t1", date="2026-01-01", amount=Decimal("300.00"), direction=TransactionDirection.CREDIT, narration="In"),
        ],
    )
    result = BankStatementValidator().validate(stmt)
    assert not result.is_valid
    assert len(result.errors) == 1
    assert result.errors[0].code == "BALANCE_RECONCILIATION_FAILED"


def test_bank_statement_validation_missing_balance_warning():
    stmt = BankStatement(
        id="s1",
        opening_balance=None,
        closing_balance=Decimal("1000.00"),
        transactions=[
            Transaction(id="t1", date="2026-01-01", amount=Decimal("100.00"), direction=TransactionDirection.CREDIT, narration="In"),
        ],
    )
    result = BankStatementValidator().validate(stmt)
    assert result.is_valid  # Warnings do not invalidate
    assert len(result.warnings) == 1
    assert result.warnings[0].code == "MISSING_OPENING_BALANCE"


def test_bank_statement_validation_empty_fails():
    stmt = BankStatement(
        id="s1",
        opening_balance=Decimal("100.00"),
        closing_balance=Decimal("100.00"),
        transactions=[],
    )
    result = BankStatementValidator().validate(stmt)
    assert not result.is_valid
    assert any(e.code == "EMPTY_STATEMENT" for e in result.errors)


def test_invoice_validation_success_and_failure():
    inv = Invoice(
        id="i1",
        invoice_number="INV-1",
        invoice_date="2026-01-01",
        total_amount=Decimal("1180.00"),
        subtotal=Decimal("1000.00"),
        lines=[InvoiceLine(id="l1", description="Service", amount=Decimal("1000.00"))],
        taxes=[Tax(id="tax:1", tax_type="GST", amount=Decimal("180.00"))],
    )
    assert InvoiceValidator().validate(inv).is_valid

    # Corrupt total
    inv_bad = Invoice(
        id="i2",
        invoice_number="INV-2",
        invoice_date="2026-01-01",
        total_amount=Decimal("500.00"),
        subtotal=Decimal("1000.00"),
        lines=[InvoiceLine(id="l1", description="Service", amount=Decimal("1000.00"))],
        taxes=[Tax(id="tax:1", tax_type="GST", amount=Decimal("180.00"))],
    )
    bad_result = InvoiceValidator().validate(inv_bad)
    assert not bad_result.is_valid
    assert any(e.code == "TOTAL_AMOUNT_MISMATCH" for e in bad_result.errors)


def test_ledger_validation_success_and_failure():
    led = Ledger(
        id="l1",
        name="Test",
        opening_balance=Decimal("500.00"),
        closing_balance=Decimal("700.00"),
        entries=[
            LedgerEntry(id="e1", date="2026-01-01", narration="d", amount=Decimal("300.00"), direction=EntryDirection.DEBIT),
            LedgerEntry(id="e2", date="2026-01-02", narration="c", amount=Decimal("100.00"), direction=EntryDirection.CREDIT),
        ],
    )
    assert LedgerValidator().validate(led).is_valid

    # Corrupt closing
    led_bad = Ledger(
        id="l2",
        name="Test Bad",
        opening_balance=Decimal("500.00"),
        closing_balance=Decimal("9999.00"),
        entries=[
            LedgerEntry(id="e1", date="2026-01-01", narration="d", amount=Decimal("100.00"), direction=EntryDirection.DEBIT),
        ],
    )
    bad_res = LedgerValidator().validate(led_bad)
    assert not bad_res.is_valid
    assert any(e.code == "LEDGER_BALANCE_MISMATCH" for e in bad_res.errors)


def test_validate_dispatcher():
    stmt = BankStatement(
        id="s1",
        opening_balance=Decimal("100.00"),
        closing_balance=Decimal("150.00"),
        transactions=[
            Transaction(id="t1", date="2026-01-01", amount=Decimal("50.00"), direction=TransactionDirection.CREDIT, narration="In"),
        ],
    )
    res = validate(stmt)
    assert res.is_valid
