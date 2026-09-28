"""Canonical InterestCertificate and TDSCertificate domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from aip_canonica.models.base import DatePeriod
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models.graph import CanonicalGraph, Relationship
from aip_canonica.models.party import Account, Party
from aip_canonica.models.provenance import Provenance

if TYPE_CHECKING:
    from aip_canonica.validation.result import ValidationResult


@dataclass(slots=True)
class InterestCertificate:
    """Canonical representation of an interest certificate issued by a bank or NBFC."""

    id: str
    interest_amount: Decimal
    institution: Party | None = None
    recipient: Party | None = None
    account: Account | None = None
    period: DatePeriod | None = None
    tds_deducted: Decimal | None = None
    certificate_number: str | None = None
    currency: str = "INR"
    provenance: Provenance | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.INTEREST_CERTIFICATE

    @property
    def node_type(self) -> str:
        return "InterestCertificate"

    def as_graph(self) -> CanonicalGraph:
        graph = CanonicalGraph()
        graph.add_node(self)

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

        return graph

    def validate(self) -> ValidationResult:
        from aip_canonica.validation.result import ValidationIssue, ValidationResult

        issues: list[ValidationIssue] = []
        if self.interest_amount < Decimal(0):
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="NEGATIVE_INTEREST",
                    message="Interest amount cannot be negative",
                    field="interest_amount",
                )
            )
        if self.tds_deducted is not None and self.tds_deducted > self.interest_amount:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="TDS_EXCEEDS_INTEREST",
                    message="TDS deducted cannot exceed total interest amount",
                    field="tds_deducted",
                )
            )
        return ValidationResult(
            is_valid=len([i for i in issues if i.severity == "error"]) == 0,
            issues=issues,
            metrics={
                "interest_amount": str(self.interest_amount),
                "tds_deducted": str(self.tds_deducted) if self.tds_deducted is not None else None,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "document_type": self.document_type.value,
            "node_type": self.node_type,
            "interest_amount": str(self.interest_amount),
            "currency": self.currency,
        }
        if self.certificate_number is not None:
            data["certificate_number"] = self.certificate_number
        if self.institution is not None:
            data["institution"] = self.institution.to_dict()
        if self.recipient is not None:
            data["recipient"] = self.recipient.to_dict()
        if self.account is not None:
            data["account"] = self.account.to_dict()
        if self.period is not None:
            data["period"] = self.period.to_dict()
        if self.tds_deducted is not None:
            data["tds_deducted"] = str(self.tds_deducted)
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        if self.metadata:
            data["metadata"] = self.metadata
        return data


@dataclass(frozen=True, slots=True)
class TDSEntry:
    """A single tax deduction record (e.g. Form 16A quarterly line)."""

    id: str
    amount_paid: Decimal
    tds_amount: Decimal
    section: str | None = None
    date_paid: str | None = None
    provenance: Provenance | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def node_type(self) -> str:
        return "TDSEntry"

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "node_type": self.node_type,
            "amount_paid": str(self.amount_paid),
            "tds_amount": str(self.tds_amount),
        }
        if self.section is not None:
            data["section"] = self.section
        if self.date_paid is not None:
            data["date_paid"] = self.date_paid
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        if self.metadata:
            data["metadata"] = self.metadata
        return data


@dataclass(slots=True)
class TDSCertificate:
    """Canonical representation of a TDS certificate (e.g. Form 16 / 16A)."""

    id: str
    certificate_number: str
    total_tds_deducted: Decimal
    deductor: Party | None = None
    deductee: Party | None = None
    financial_year: str | None = None
    assessment_year: str | None = None
    total_amount_paid: Decimal | None = None
    entries: list[TDSEntry] = field(default_factory=list)
    provenance: Provenance | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.TDS_CERTIFICATE

    @property
    def node_type(self) -> str:
        return "TDSCertificate"

    def as_graph(self) -> CanonicalGraph:
        graph = CanonicalGraph()
        graph.add_node(self)

        if self.deductor is not None:
            graph.add_node(self.deductor)
            graph.add_relationship(
                Relationship(
                    source_id=self.id,
                    relation="deductor",
                    target_id=self.deductor.id,
                    target_type="Party",
                )
            )

        if self.deductee is not None:
            graph.add_node(self.deductee)
            graph.add_relationship(
                Relationship(
                    source_id=self.id,
                    relation="deductee",
                    target_id=self.deductee.id,
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
                    target_type="TDSEntry",
                )
            )

        return graph

    def validate(self) -> ValidationResult:
        from aip_canonica.validation.result import ValidationIssue, ValidationResult

        issues: list[ValidationIssue] = []
        if self.entries:
            sum_tds = sum(e.tds_amount for e in self.entries)
            if abs(sum_tds - self.total_tds_deducted) > Decimal("0.01"):
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="TDS_SUM_MISMATCH",
                        message=f"Sum of TDS entries ({sum_tds}) does not equal stated total ({self.total_tds_deducted})",
                        field="total_tds_deducted",
                        details={"sum_entries": str(sum_tds), "stated": str(self.total_tds_deducted)},
                    )
                )
        return ValidationResult(
            is_valid=len([i for i in issues if i.severity == "error"]) == 0,
            issues=issues,
            metrics={
                "entry_count": len(self.entries),
                "total_tds_deducted": str(self.total_tds_deducted),
            },
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "document_type": self.document_type.value,
            "node_type": self.node_type,
            "certificate_number": self.certificate_number,
            "total_tds_deducted": str(self.total_tds_deducted),
            "entry_count": len(self.entries),
            "entries": [e.to_dict() for e in self.entries],
        }
        if self.deductor is not None:
            data["deductor"] = self.deductor.to_dict()
        if self.deductee is not None:
            data["deductee"] = self.deductee.to_dict()
        if self.financial_year is not None:
            data["financial_year"] = self.financial_year
        if self.assessment_year is not None:
            data["assessment_year"] = self.assessment_year
        if self.total_amount_paid is not None:
            data["total_amount_paid"] = str(self.total_amount_paid)
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        if self.metadata:
            data["metadata"] = self.metadata
        return data
