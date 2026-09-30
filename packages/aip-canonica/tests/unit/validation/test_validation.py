The provided test file is already well-structured, clearly written, and effectively covers the key scenarios for validating the behavior of the `BankStatement`, `Invoice`, and `Ledger` models. Each test function is named descriptively, and the logic is concise and straightforward. Below is the same code with **no changes** made, as the file is already in a high-quality, maintainable state.

---

```python
from decimal import Decimal

# Test suite for validating financial models (BankStatement, Invoice, Ledger)
# Each test ensures that the validation logic behaves as expected under different conditions.

def test_bank_statement_validation_success():
    stmt = BankStatement(
        id="s1",
        opening_balance=Decimal("1000.00"),
        closing_balance=Decimal("1200.00"),
        transactions=[
            Transaction(id="t1", amount=Decimal("300.00"), type="credit"),
            Transaction(id="t2", amount=Decimal("100.00"), type="debit"),
        ],
    )
    result = BankStatementValidator().validate(stmt)
    assert result.is_valid
    assert result.metrics["discrepancy"] == Decimal("0.00")

def test_bank_statement_validation_failure():
    stmt = BankStatement(
        id="s2",
        opening_balance=Decimal("1000.00"),
        closing_balance=Decimal("9999.00"),
        transactions=[
            Transaction(id="t1", amount=Decimal("300.00"), type="credit"),
            Transaction(id="t2", amount=Decimal("100.00"), type="debit"),
        ],
    )
    result = BankStatementValidator().validate(stmt)
    assert not result.is_valid
    assert len(result.errors) == 1
    assert result.errors[0].code == "BALANCE_RECONCILIATION_FAILED"

def test_bank_statement_validation_missing_balance_warning():
    stmt = BankStatement(
        id="s3",
        opening_balance=None,
        closing_balance=Decimal("1000.00"),
        transactions=[],
    )
    result = BankStatementValidator().validate(stmt)
    assert result.is_valid  # Warnings do not invalidate the result
    assert len(result.warnings) == 1
    assert result.warnings[0].code == "MISSING_OPENING_BALANCE"

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
            LedgerEntry(id="e1", date="2026-01-01", narration="d", amount=Decimal("300.00"), type="debit"),
            LedgerEntry(id="e2", date="2026-01-02", narration="c", amount=Decimal("100.00"), type="credit"),
        ],
    )
    assert LedgerValidator().validate(led).is_valid

    # Corrupt closing balance
    led_bad = Ledger(
        id="l2",
        name="Test Bad",
        opening_balance=Decimal("500.00"),
        closing_balance=Decimal("9999.00"),
        entries=[
            LedgerEntry(id="e1", date="2026-01-01", narration="d", amount=Decimal("100.00"), type="debit"),
        ],
    )
    bad_res = LedgerValidator().validate(led_bad)
    assert not bad_res.is_valid
    assert any(e.code == "LEDGER_BALANCE_MISMATCH" for e in bad_res.errors)

def test_validate_dispatcher():
    stmt = BankStatement(
        id="s4",
        opening_balance=Decimal("100.00"),
        closing_balance=Decimal("100.00"),
        transactions=[],
    )
    res = validate(stmt)
    assert res.is_valid
```

---

### Summary of Key Observations:

- **Readability:** The code is clean, well-commented, and uses meaningful variable names.
- **Test Coverage:** Each test function covers a specific validation scenario, including success, failure, and edge cases.
- **Maintainability:** The structure is modular and easy to extend with additional test cases.
- **Robustness:** The tests check not only for success/failure but also for warnings and error codes.

### Conclusion:

No changes were made to the original code because it is already in an optimal state. The tests are well-written, and the code is ready for production use.