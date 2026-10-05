"""Deterministic financial validation engine for canonical documents."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from aip_canonica.models.base import CanonicalDocument, TransactionDirection
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models.ledger import EntryDirection
from aip_canonica.validation.result import ValidationIssue, ValidationResult

if TYPE_CHECKING:
    from aip_canonica.models.bank_statement import BankStatement
    from aip_canonica.models.invoice import Invoice
    from aip_canonica.models.ledger import Ledger


TOLERANCE = Decimal("0.05")


class BankStatementValidator:
    """Validates the mathematical and structural integrity of a bank statement.

    Ensures that all transactions are valid, balances reconcile, and required fields are present.
    """

    def validate(self, document: BankStatement) -> ValidationResult:
        """Perform validation on a bank statement document."""
        issues = []
        metrics = {}

        # Check for required data
        if not document.transactions:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="EMPTY_TRANSACTIONS",
                    message="Bank statement must contain at least one transaction",
                    field="transactions",
                )
            )

        # Process transactions
        total_debits = Decimal("0")
        total_credits = Decimal("0")

        for transaction in document.transactions:
            if transaction.amount < 0:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="NEGATIVE_TRANSACTION",
                        message="Transaction amount cannot be negative",
                        field="transactions",
                        details={"transaction_id": transaction.id, "amount": transaction.amount},
                    )
                )

            if transaction.direction == TransactionDirection.DEBIT:
                total_debits += transaction.amount
            else:
                total_credits += transaction.amount

        # Build metrics
        metrics["transaction_count"] = str(len(document.transactions))
        metrics["total_debits"] = str(total_debits)
        metrics["total_credits"] = str(total_credits)

        # Validate balances
        if document.opening_balance is not None and document.closing_balance is not None:
            expected_closing = document.opening_balance + total_debits - total_credits
            difference = abs(expected_closing - document.closing_balance)

            if difference > TOLERANCE:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="BALANCE_MISMATCH",
                        message="Calculated closing balance does not match reported value",
                        field="closing_balance",
                        details={
                            "opening_balance": document.opening_balance,
                            "total_debits": total_debits,
                            "total_credits": total_credits,
                            "expected_closing": expected_closing,
                            "actual_closing": document.closing_balance,
                            "difference": difference,
                        },
                    )
                )

        # Return validation result
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            metrics=metrics,
        )


class InvoiceValidator:
    """Validates the mathematical and structural integrity of an invoice.

    Ensures that all line items are valid, totals reconcile, and required fields are present.
    """

    def validate(self, document: Invoice) -> ValidationResult:
        """Perform validation on an invoice document."""
        issues = []
        metrics = {}

        # Check for required data
        if not document.line_items:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="EMPTY_LINE_ITEMS",
                    message="Invoice must contain at least one line item",
                    field="line_items",
                )
            )

        # Process line items
        total_amount = Decimal("0")

        for item in document.line_items:
            if item.amount < 0:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="NEGATIVE_LINE_ITEM",
                        message="Line item amount cannot be negative",
                        field="line_items",
                        details={"item_id": item.id, "amount": item.amount},
                    )
                )

            total_amount += item.amount

        # Build metrics
        metrics["line_item_count"] = str(len(document.line_items))
        metrics["total_amount"] = str(total_amount)

        # Validate totals
        if document.total_amount is not None:
            difference = abs(total_amount - document.total_amount)

            if difference > TOLERANCE:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="TOTAL_MISMATCH",
                        message="Calculated total amount does not match reported value",
                        field="total_amount",
                        details={
                            "expected_total": total_amount,
                            "actual_total": document.total_amount,
                            "difference": difference,
                        },
                    )
                )

        # Return validation result
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            metrics=metrics,
        )


class LedgerValidator:
    """Validates the mathematical and structural integrity of a ledger.

    Ensures that all entries are valid, balances reconcile, and required fields are present.
    """

    def validate(self, document: Ledger) -> ValidationResult:
        """Perform validation on a ledger document."""
        issues = []
        metrics = {}

        # Check for required data
        if not document.entries:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="EMPTY_ENTRIES",
                    message="Ledger must contain at least one entry",
                    field="entries",
                )
            )

        # Process entries
        total_debits = Decimal("0")
        total_credits = Decimal("0")

        for entry in document.entries:
            if entry.amount < 0:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="NEGATIVE_ENTRY",
                        message="Entry amount cannot be negative",
                        field="entries",
                        details={"entry_id": entry.id, "amount": entry.amount},
                    )
                )

            if entry.direction == EntryDirection.DEBIT:
                total_debits += entry.amount
            else:
                total_credits += entry.amount

        # Build metrics
        metrics["entry_count"] = str(len(document.entries))
        metrics["total_debits"] = str(total_debits)
        metrics["total_credits"] = str(total_credits)

        # Validate balances
        if document.opening_balance is not None and document.closing_balance is not None:
            # Calculate expected closing balance based on account type
            if document.account_type in ["asset", "expense"]:
                expected_closing = document.opening_balance + total_debits - total_credits
            elif document.account_type in ["liability", "equity", "income"]:
                expected_closing = document.opening_balance - total_debits + total_credits
            else:
                expected_closing = None

            if expected_closing is not None:
                difference = abs(expected_closing - document.closing_balance)

                if difference > TOLERANCE:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="BALANCE_MISMATCH",
                            message="Calculated closing balance does not match reported value",
                            field="closing_balance",
                            details={
                                "account_type": document.account_type,
                                "opening_balance": document.opening_balance,
                                "total_debits": total_debits,
                                "total_credits": total_credits,
                                "expected_closing": expected_closing,
                                "actual_closing": document.closing_balance,
                                "difference": difference,
                            },
                        )
                    )

        # Return validation result
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            metrics=metrics,
        )


def validate(document: CanonicalDocument) -> ValidationResult:
    """Deterministic validation dispatcher for any canonical document.

    Routes validation to the appropriate document-specific validator based on type.
    """
    doc_type = document.document_type

    if doc_type == DocumentType.BANK_STATEMENT:
        return BankStatementValidator().validate(document)  # type: ignore[arg-type]
    elif doc_type == DocumentType.INVOICE:
        return InvoiceValidator().validate(document)  # type: ignore[arg-type]
    elif doc_type == DocumentType.LEDGER:
        return LedgerValidator().validate(document)  # type: ignore[arg-type]
    else:
        # Fallback to document's own validation method
        return document.validate()


class FinancialValidator:
    """Convenience facade for deterministic financial validation.

    Provides a unified interface for validating any canonical document.
    """

    @staticmethod
    def validate(document: CanonicalDocument) -> ValidationResult:
        """Validate a canonical document using the appropriate validator.

        This method serves as a simple facade to the document-specific validation logic.
        """
        return validate(document)