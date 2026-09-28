"""Canonical BankStatement and Transaction domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from aip_canonica.models.base import DatePeriod, TransactionDirection
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models.graph import CanonicalGraph, Relationship
from aip_canonica.models.party import Account, Party
from aip_canonica.models.provenance import Provenance

if TYPE_CHECKING:
    from aip_canonica.validation.result import ValidationResult


@dataclass(frozen=True, slots=True)
class Transaction:
    """A single financial movement on a bank statement."""

    id: str
    date: str
    amount: Decimal
    direction: TransactionDirection
    narration: str
    value_date: str | None = None
    currency: str = "INR"
    balance: Decimal | None = None
    reference: str | None = None
    counterparty: Party | None = None
    provenance: Provenance | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def node_type(self) -> str:
        return "Transaction"

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "node_type": self.node_type,
            "date": self.date,
            "amount": str(self.amount),
            "direction": self.direction.value,
            "currency": self.currency,
            "narration": self.narration,
        }
        if self.value_date is not None:
            data["value_date"] = self.value_date
        if self.balance is not None:
            data["balance"] = str(self.balance)
        if self.reference is not None:
            data["reference"] = self.reference
        if self.counterparty is not None:
            data["counterparty"] = self.counterparty.to_dict()
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        if self.metadata:
            data["metadata"] = self.metadata
        return data


@dataclass(slots=True)
class BankStatement:
    """Canonical representation of a bank account statement."""

    id: str
    account: Account | None = None
    holder: Party | None = None
    institution: Party | None = None
    period: DatePeriod | None = None
    opening_balance: Decimal | None = None
    closing_balance: Decimal | None = None
    currency: str = "INR"
    transactions: list[Transaction] = field(default_factory=list)
    provenance: Provenance | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.BANK_STATEMENT

    @property
    def node_type(self) -> str:
        return "BankStatement"

    @property
    def account_number(self) -> str | None:
        return self.account.account_number if self.account is not None else None

    def as_graph(self) -> CanonicalGraph:
        """Construct a directed graph connecting statement, accounts, parties, and transactions."""
        graph = CanonicalGraph()
        graph.add_node(self)

        if self.account is not None:
            graph.add_node(self.account)
            graph.add_relationship(
                Relationship(
                    source_id=self.id,
                    relation="account",
                    target_id=self.account.id,
                    target_type="Account",
                )
            )

        if self.holder is not None:
            graph.add_node(self.holder)
            graph.add_relationship(
                Relationship(
                    source_id=self.id,
                    relation="holder",
                    target_id=self.holder.id,
                    target_type="Party",
                )
            )

        if self.institution is not None:
            graph.add_node(self.institution)
            graph.add_relationship(
                Relationship(
                    source_id=self.id,
                    relation="institution",
                    target_id=self.institution.id,
                    target_type="Party",
                )
            )

        for txn in self.transactions:
            graph.add_node(txn)
            graph.add_relationship(
                Relationship(
                    source_id=self.id,
                    relation="contains",
                    target_id=txn.id,
                    target_type="Transaction",
                )
            )
            if txn.counterparty is not None:
                graph.add_node(txn.counterparty)
                graph.add_relationship(
                    Relationship(
                        source_id=txn.id,
                        relation="counterparty",
                        target_id=txn.counterparty.id,
                        target_type="Party",
                    )
                )

        return graph

    def validate(self) -> ValidationResult:
        """Deterministic financial reconciliation of opening + deposits - withdrawals ≈ closing."""
        from aip_canonica.validation.validator import BankStatementValidator

        return BankStatementValidator().validate(self)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "document_type": self.document_type.value,
            "node_type": self.node_type,
            "currency": self.currency,
            "transaction_count": len(self.transactions),
            "transactions": [t.to_dict() for t in self.transactions],
        }
        if self.account is not None:
            data["account"] = self.account.to_dict()
        if self.holder is not None:
            data["holder"] = self.holder.to_dict()
        if self.institution is not None:
            data["institution"] = self.institution.to_dict()
        if self.period is not None:
            data["period"] = self.period.to_dict()
        if self.opening_balance is not None:
            data["opening_balance"] = str(self.opening_balance)
        if self.closing_balance is not None:
            data["closing_balance"] = str(self.closing_balance)
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        if self.metadata:
            data["metadata"] = self.metadata
        return data
