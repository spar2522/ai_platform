"""Canonical Ledger and LedgerEntry domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any

from aip_canonica.models.base import DatePeriod
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models.graph import CanonicalGraph, Relationship
from aip_canonica.models.party import Account, Party
from aip_canonica.models.provenance import Provenance

if TYPE_CHECKING:
    from aip_canonica.validation.result import ValidationResult


class EntryDirection(str, Enum):
    """Debit or Credit direction of a ledger movement."""

    DEBIT = "debit"
    CREDIT = "credit"


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    """A single journal or ledger posting."""

    id: str
    date: str
    narration: str
    amount: Decimal
    direction: EntryDirection
    balance: Decimal | None = None
    reference: str | None = None
    counterparty: Party | None = None
    provenance: Provenance | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def node_type(self) -> str:
        return "LedgerEntry"

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "node_type": self.node_type,
            "date": self.date,
            "narration": self.narration,
            "amount": str(self.amount),
            "direction": self.direction.value,
        }
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
class Ledger:
    """Canonical representation of an accounting general ledger or sub-ledger."""

    id: str
    name: str
    account: Account | None = None
    party: Party | None = None
    period: DatePeriod | None = None
    opening_balance: Decimal | None = None
    closing_balance: Decimal | None = None
    currency: str = "INR"
    entries: list[LedgerEntry] = field(default_factory=list)
    provenance: Provenance | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.LEDGER

    @property
    def node_type(self) -> str:
        return "Ledger"

    def as_graph(self) -> CanonicalGraph:
        """Construct a directed graph connecting ledger, account, party, and entries."""
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

        if self.party is not None:
            graph.add_node(self.party)
            graph.add_relationship(
                Relationship(
                    source_id=self.id,
                    relation="party",
                    target_id=self.party.id,
                    target_type="Party",
                )
            )

        for entry in self.entries:
            graph.add_node(entry)
            graph.add_relationship(
                Relationship(
                    source_id=self.id,
                    relation="contains",
                    target_id=entry.id,
                    target_type="LedgerEntry",
                )
            )
            if entry.counterparty is not None:
                graph.add_node(entry.counterparty)
                graph.add_relationship(
                    Relationship(
                        source_id=entry.id,
                        relation="counterparty",
                        target_id=entry.counterparty.id,
                        target_type="Party",
                    )
                )

        return graph

    def validate(self) -> ValidationResult:
        """Deterministic reconciliation of opening + debits - credits ≈ closing."""
        from aip_canonica.validation.validator import LedgerValidator

        return LedgerValidator().validate(self)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "document_type": self.document_type.value,
            "node_type": self.node_type,
            "name": self.name,
            "currency": self.currency,
            "entry_count": len(self.entries),
            "entries": [e.to_dict() for e in self.entries],
        }
        if self.account is not None:
            data["account"] = self.account.to_dict()
        if self.party is not None:
            data["party"] = self.party.to_dict()
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
