```python
import pytest
from decimal import Decimal
from your_module.models import BankStatement, Transaction
from your_module.validators import BankStatementValidator


def test_bank_statement_validation_success():
    stmt = BankStatement(
        opening_balance=Decimal("1000.00"),
        closing_balance=Decimal("1050.00"),
        transactions=[
            Transaction(
                date="2023-01-01",
                amount=Decimal("50.00"),
                description="Interest",
                balance=Decimal("1050.00"),
            ),
        ],
    )
    res = BankStatementValidator().validate(stmt)
    assert res.is_valid
    assert res.metrics["discrepancy"] == "0.00"


def test_bank_statement_validation_failure():
    stmt = BankStatement(
        opening_balance=Decimal("1000.00"),
        closing_balance=Decimal("9999.00"),
        transactions=[
            Transaction(
                date="2023-01-01",
                amount=Decimal("50.00"),
                description="Interest",
                balance=Decimal("1050.00"),
            ),
        ],
    )
    res = BankStatementValidator().validate(stmt)
    assert not res.is_valid
    assert any(e.code == "BALANCE_MISMATCH" for e in res.errors)


def test_bank_statement_validation_empty_transactions():
    stmt = BankStatement(
        opening_balance=Decimal("1000.00"),
        closing_balance=Decimal("1000.00"),
        transactions=[],
    )
    res = BankStatementValidator().validate(stmt)
    assert not res.is_valid
    assert any(e.code == "EMPTY_STATEMENT" for e in res.errors)


def test_bank_statement_validation_missing_transaction_date():
    stmt = BankStatement(
        opening_balance=Decimal("1000.00"),
        closing_balance=Decimal("1050.00"),
        transactions=[
            Transaction(
                date=None,
                amount=Decimal("50.00"),
                description="Interest",
                balance=Decimal("1050.00"),
            ),
        ],
    )
    res = BankStatementValidator().validate(stmt)
    assert not res.is_valid
    assert any(e.code == "MISSING_TRANSACTION_DATE" for e in res.errors)


def test_bank_statement_validation_no_balance_information():
    stmt = BankStatement(
        opening_balance=None,
        closing_balance=None,
        transactions=[
            Transaction(
                date="2023-01-01",
                amount=Decimal("50.00"),
                description="Interest",
                balance=None,
            ),
        ],
    )
    res = BankStatementValidator().validate(stmt)
    assert not res.is_valid
    assert any(e.code == "NO_BALANCE_INFORMATION" for e in res.errors)


def test_bank_statement_validation_missing_opening_balance_warning():
    stmt = BankStatement(
        opening_balance=None,
        closing_balance=Decimal("1050.00"),
        transactions=[
            Transaction(
                date="2023-01-01",
                amount=Decimal("50.00"),
                description="Interest",
                balance=Decimal("1050.00"),
            ),
        ],
    )
    res = BankStatementValidator().validate(stmt)
    assert res.is_valid
    assert any(e.code == "MISSING_OPENING_BALANCE" for e in res.warnings)


def test_invoice_validation_success_and_failure():
    # Test setup for invoice validation
    pass


def test_ledger_validation_success_and_failure():
    # Test setup for ledger validation
    pass


def test_validate_dispatcher():
    stmt = BankStatement(
        opening_balance=Decimal("1000.00"),
        closing_balance=Decimal("1050.00"),
        transactions=[
            Transaction(
                date="2023-01-01",
                amount=Decimal("50.00"),
                description="Interest",
                balance=Decimal("1050.00"),
            ),
        ],
    )
    res = BankStatementValidator().validate(stmt)
    assert res.is_valid
```