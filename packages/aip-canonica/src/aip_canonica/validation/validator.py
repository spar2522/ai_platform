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
    """Validates financial reconciliation on a BankStatement:

    opening_balance + total_credits - total_debits ≈ closing_balance
    """

    def validate(self, statement: BankStatement) -> ValidationResult:
        issues: list[ValidationIssue] = []

        if not statement.transactions:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="EMPTY_STATEMENT",
                    message="Bank statement contains no transactions",
                    field="transactions",
                )
            )

        total_credits = Decimal("0")
        total_debits = Decimal("0")

        for idx, txn in enumerate(statement.transactions):
            if txn.amount < Decimal("0"):
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="NEGATIVE_TRANSACTION_AMOUNT",
                        message=f"Transaction {txn.id} has negative amount {txn.amount}",
                        field="amount",
                        details={"transaction_id": txn.id, "amount": str(txn.amount)},
                    )
                )

            if txn.direction == TransactionDirection.CREDIT:
                total_credits += txn.amount
            elif txn.direction == TransactionDirection.DEBIT:
                total_debits += txn.amount

        metrics: dict[str, str] = {
            "transaction_count": str(len(statement.transactions)),
            "total_credits": str(total_credits),
            "total_debits": str(total_debits),
        }

        if statement.opening_balance is not None and statement.closing_balance is not None:
            expected_closing = statement.opening_balance + total_credits - total_debits
            diff = abs(expected_closing - statement.closing_balance)

            metrics["opening_balance"] = str(statement.opening_balance)
            metrics["stated_closing_balance"] = str(statement.closing_balance)
            metrics["calculated_closing_balance"] = str(expected_closing)
            metrics["discrepancy"] = str(diff)

            if diff > TOLERANCE:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="BALANCE_RECONCILIATION_FAILED",
                        message=(
                            f"Closing balance mismatch: opening ({statement.opening_balance}) + "
                            f"credits ({total_credits}) - debits ({total_debits}) = "
                            f"{expected_closing}, but statement states {statement.closing_balance}"
                        ),
                        field="closing_balance",
                        details={
                            "opening": str(statement.opening_balance),
                            "credits": str(total_credits),
                            "debits": str(total_debits),
                            "expected_closing": str(expected_closing),
                            "stated_closing": str(statement.closing_balance),
                            "discrepancy": str(diff),
                        },
                    )
                )
        else:
            if statement.opening_balance is None:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="MISSING_OPENING_BALANCE",
                        message="Statement opening balance is not available for full reconciliation",
                        field="opening_balance",
                    )
                )
            if statement.closing_balance is None:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="MISSING_CLOSING_BALANCE",
                        message="Statement closing balance is not available for full reconciliation",
                        field="closing_balance",
                    )
                )

        is_valid = len([i for i in issues if i.severity == "error"]) == 0
        return ValidationResult(is_valid=is_valid, issues=issues, metrics=metrics)


class InvoiceValidator:
    """Validates mathematical consistency on an Invoice:

    lines + taxes - discounts ≈ total_amount
    """

    def validate(self, invoice: Invoice) -> ValidationResult:
        issues: list[ValidationIssue] = []

        if not invoice.lines:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="EMPTY_INVOICE",
                    message="Invoice contains no line items",
                    field="lines",
                )
            )

        sum_lines = sum((line.amount for line in invoice.lines), Decimal("0"))
        sum_taxes = sum((t.amount for t in invoice.taxes), Decimal("0"))
        sum_discounts = sum((d.amount for d in invoice.discounts), Decimal("0"))

        metrics: dict[str, str] = {
            "line_count": str(len(invoice.lines)),
            "sum_lines": str(sum_lines),
            "sum_taxes": str(sum_taxes),
            "sum_discounts": str(sum_discounts),
            "stated_total": str(invoice.total_amount),
        }

        # Check line item subtotal if stated
        if invoice.subtotal is not None and invoice.lines:
            subtotal_diff = abs(sum_lines - invoice.subtotal)
            if subtotal_diff > TOLERANCE:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="SUBTOTAL_MISMATCH",
                        message=(
                            f"Sum of lines ({sum_lines}) does not match stated subtotal ({invoice.subtotal})"
                        ),
                        field="subtotal",
                        details={"sum_lines": str(sum_lines), "stated_subtotal": str(invoice.subtotal)},
                    )
                )

        base_amount = invoice.subtotal if invoice.subtotal is not None else sum_lines
        expected_total = base_amount + sum_taxes - sum_discounts
        diff = abs(expected_total - invoice.total_amount)

        metrics["calculated_total"] = str(expected_total)
        metrics["discrepancy"] = str(diff)

        if diff > TOLERANCE:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="TOTAL_AMOUNT_MISMATCH",
                    message=(
                        f"Calculated total ({expected_total}) from subtotal ({base_amount}) + "
                        f"taxes ({sum_taxes}) - discounts ({sum_discounts}) does not match "
                        f"stated total ({invoice.total_amount})"
                    ),
                    field="total_amount",
                    details={
                        "expected_total": str(expected_total),
                        "stated_total": str(invoice.total_amount),
                        "discrepancy": str(diff),
                    },
                )
            )

        is_valid = len([i for i in issues if i.severity == "error"]) == 0
        return ValidationResult(is_valid=is_valid, issues=issues, metrics=metrics)


class LedgerValidator:
    """Validates mathematical integrity of a Ledger:

    opening_balance + total_movements ≈ closing_balance
    """

    def validate(self, ledger: Ledger) -> ValidationResult:
        issues: list[ValidationIssue] = []

        if not ledger.entries:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="EMPTY_LEDGER",
                    message="Ledger contains no entries",
                    field="entries",
                )
            )

        total_debits = Decimal("0")
        total_credits = Decimal("0")

        for entry in ledger.entries:
            if entry.direction == EntryDirection.DEBIT:
                total_debits += entry.amount
            elif entry.direction == EntryDirection.CREDIT:
                total_credits += entry.amount

        metrics: dict[str, str] = {
            "entry_count": str(len(ledger.entries)),
            "total_debits": str(total_debits),
            "total_credits": str(total_credits),
        }

        if ledger.opening_balance is not None and ledger.closing_balance is not None:
            # Asset/Expense normal: opening + debit - credit
            normal_asset_closing = ledger.opening_balance + total_debits - total_credits
            # Liability/Equity/Income normal: opening + credit - debit
            normal_liability_closing = ledger.opening_balance - total_debits + total_credits

            diff1 = abs(normal_asset_closing - ledger.closing_balance)
            diff2 = abs(normal_liability_closing - ledger.closing_balance)

            min_diff = min(diff1, diff2)
            metrics["opening_balance"] = str(ledger.opening_balance)
            metrics["stated_closing_balance"] = str(ledger.closing_balance)
            metrics["calculated_closing_balance"] = str(normal_asset_closing if diff1 <= diff2 else normal_liability_closing)
            metrics["discrepancy"] = str(min_diff)

            if min_diff > TOLERANCE:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="LEDGER_BALANCE_MISMATCH",
                        message=(
                            f"Ledger closing balance mismatch: opening ({ledger.opening_balance}) with "
                            f"debits ({total_debits}) and credits ({total_credits}) does not match "
                            f"closing ({ledger.closing_balance})"
                        ),
                        field="closing_balance",
                        details={
                            "opening": str(ledger.opening_balance),
                            "debits": str(total_debits),
                            "credits": str(total_credits),
                            "stated_closing": str(ledger.closing_balance),
                        },
                    )
                )

        is_valid = len([i for i in issues if i.severity == "error"]) == 0
        return ValidationResult(is_valid=is_valid, issues=issues, metrics=metrics)


def validate(document: CanonicalDocument) -> ValidationResult:
    """Deterministic validation dispatcher for any canonical document."""
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
    """Convenience facade for deterministic financial validation."""

    @staticmethod
    def validate(document: CanonicalDocument) -> ValidationResult:
        return validate(document)
