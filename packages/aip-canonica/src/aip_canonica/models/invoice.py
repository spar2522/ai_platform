"""Canonical Invoice and line item domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from aip_canonica.models.document_type import DocumentType
from aip_canonica.models.graph import CanonicalGraph, Relationship
from aip_canonica.models.party import Party
from aip_canonica.models.provenance import Provenance

if TYPE_CHECKING:
    from aip_canonica.validation.result import ValidationResult


@dataclass(frozen=True, slots=True)
class Tax:
    """Tax charge on an invoice or invoice line item."""

    id: str
    tax_type: str
    amount: Decimal
    rate: Decimal | None = None
    provenance: Provenance | None = None

    @property
    def node_type(self) -> str:
        return "Tax"

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "node_type": self.node_type,
            "tax_type": self.tax_type,
            "amount": str(self.amount),
        }
        if self.rate is not None:
            data["rate"] = str(self.rate)
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        return data


@dataclass(frozen=True, slots=True)
class Discount:
    """Discount applied to an invoice or invoice line item."""

    id: str
    amount: Decimal
    description: str = ""
    rate: Decimal | None = None
    provenance: Provenance | None = None

    @property
    def node_type(self) -> str:
        return "Discount"

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "node_type": self.node_type,
            "amount": str(self.amount),
            "description": self.description,
        }
        if self.rate is not None:
            data["rate"] = str(self.rate)
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        return data


@dataclass(frozen=True, slots=True)
class InvoiceLine:
    """An individual line item within an invoice."""

    id: str
    description: str
    amount: Decimal
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    tax: Tax | None = None
    discount: Discount | None = None
    hsn_sac: str | None = None
    provenance: Provenance | None = None

    @property
    def node_type(self) -> str:
        return "InvoiceLine"

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "node_type": self.node_type,
            "description": self.description,
            "amount": str(self.amount),
        }
        if self.quantity is not None:
            data["quantity"] = str(self.quantity)
        if self.unit_price is not None:
            data["unit_price"] = str(self.unit_price)
        if self.tax is not None:
            data["tax"] = self.tax.to_dict()
        if self.discount is not None:
            data["discount"] = self.discount.to_dict()
        if self.hsn_sac is not None:
            data["hsn_sac"] = self.hsn_sac
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        return data


@dataclass(slots=True)
class Invoice:
    """Generic canonical Invoice model representing both sales and purchase documents."""

    id: str
    invoice_number: str
    invoice_date: str
    total_amount: Decimal
    issuer: Party | None = None
    recipient: Party | None = None
    due_date: str | None = None
    currency: str = "INR"
    lines: list[InvoiceLine] = field(default_factory=list)
    taxes: list[Tax] = field(default_factory=list)
    discounts: list[Discount] = field(default_factory=list)
    subtotal: Decimal | None = None
    tax_total: Decimal | None = None
    discount_total: Decimal | None = None
    references: list[str] = field(default_factory=list)
    provenance: Provenance | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.INVOICE

    @property
    def node_type(self) -> str:
        return "Invoice"

    @property
    def line_items(self) -> list[InvoiceLine]:
        return self.lines

    def as_graph(self) -> CanonicalGraph:
        """Construct a directed graph connecting invoice, parties, lines, and taxes."""
        graph = CanonicalGraph()
        graph.add_node(self)

        if self.issuer is not None:
            graph.add_node(self.issuer)
            graph.add_relationship(
                Relationship(
                    source_id=self.id,
                    relation="issuer",
                    target_id=self.issuer.id,
                    target_type="Party",
                )
            )

        if self.recipient is not None:
            graph.add_node(self.recipient)
            graph.add_relationship(
                Relationship(
                    source_id=self.id,
                    relation="recipient",
                    target_id=self.recipient.id,
                    target_type="Party",
                )
            )

        for line in self.lines:
            graph.add_node(line)
            graph.add_relationship(
                Relationship(
                    source_id=self.id,
                    relation="contains",
                    target_id=line.id,
                    target_type="InvoiceLine",
                )
            )
            if line.tax is not None:
                graph.add_node(line.tax)
                graph.add_relationship(
                    Relationship(
                        source_id=line.id,
                        relation="tax",
                        target_id=line.tax.id,
                        target_type="Tax",
                    )
                )

        for tax in self.taxes:
            graph.add_node(tax)
            graph.add_relationship(
                Relationship(
                    source_id=self.id,
                    relation="tax",
                    target_id=tax.id,
                    target_type="Tax",
                )
            )

        for disc in self.discounts:
            graph.add_node(disc)
            graph.add_relationship(
                Relationship(
                    source_id=self.id,
                    relation="discount",
                    target_id=disc.id,
                    target_type="Discount",
                )
            )

        return graph

    def validate(self) -> ValidationResult:
        """Deterministic reconciliation of lines + taxes - discounts ≈ total_amount."""
        from aip_canonica.validation.validator import InvoiceValidator

        return InvoiceValidator().validate(self)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "document_type": self.document_type.value,
            "node_type": self.node_type,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date,
            "currency": self.currency,
            "total_amount": str(self.total_amount),
            "lines": [line.to_dict() for line in self.lines],
            "taxes": [t.to_dict() for t in self.taxes],
            "discounts": [d.to_dict() for d in self.discounts],
            "references": self.references,
        }
        if self.issuer is not None:
            data["issuer"] = self.issuer.to_dict()
        if self.recipient is not None:
            data["recipient"] = self.recipient.to_dict()
        if self.due_date is not None:
            data["due_date"] = self.due_date
        if self.subtotal is not None:
            data["subtotal"] = str(self.subtotal)
        if self.tax_total is not None:
            data["tax_total"] = str(self.tax_total)
        if self.discount_total is not None:
            data["discount_total"] = str(self.discount_total)
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        if self.metadata:
            data["metadata"] = self.metadata
        return data
