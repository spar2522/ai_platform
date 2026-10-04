"""Base protocols and shared types for canonical models."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from aip_canonica.models.document_type import DocumentType
from aip_canonica.models.provenance import Provenance

if TYPE_CHECKING:
    from aip_canonica.models.graph import CanonicalGraph
    from aip_canonica.validation.result import ValidationResult


class TransactionDirection(str, Enum):
    """Direction of money movement."""

    CREDIT = "credit"
    DEBIT = "debit"


@dataclass(frozen=True, slots=True)
class DatePeriod:
    """A date range representing a statement or certificate period."""

    start_date: str
    end_date: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
        }


@dataclass(frozen=True, slots=True)
class Money:
    """Monetary amount with currency."""

    amount: Decimal
    currency: str = "INR"

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount": str(self.amount),
            "currency": self.currency,
        }


@runtime_checkable
class CanonicalNode(Protocol):
    """Protocol for any node in the canonical graph."""

    @property
    def id(self) -> str:
        """Stable node identity."""
        ...

    @property
    def node_type(self) -> str:
        """Node type name."""
        ...

    @property
    def provenance(self) -> Provenance | None:
        """Source provenance for this node."""
        ...

    def to_dict(self) -> dict[str, Any]:
        """Convert node to a dictionary representation."""
        ...


@runtime_checkable
class CanonicalDocument(CanonicalNode, Protocol):
    """Protocol for a top-level canonical financial document."""

    @property
    def document_type(self) -> DocumentType:
        """The canonical document type."""
        ...

    @property
    def metadata(self) -> dict[str, Any]:
        """Extensible metadata dictionary."""
        ...

    def as_graph(self) -> CanonicalGraph:
        """Construct the canonical directed graph."""
        ...

    def validate(self) -> ValidationResult:
        """Perform deterministic financial validation."""
        ...
