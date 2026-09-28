"""Validation result data structures."""

from __future__ import annotations

import dataclasses as dc
from typing import Any, Literal

Severity = Literal["error", "warning"]


@dc.dataclass(frozen=True, slots=True)
class ValidationIssue:
    """A single issue discovered during deterministic financial validation."""

    severity: Literal["error", "warning"]
    code: str
    message: str
    field: str | None = None
    details: dict[str, Any] = dc.field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.field is not None:
            data["field"] = self.field
        if self.details:
            data["details"] = self.details
        return data


Finding = ValidationIssue


@dc.dataclass(slots=True)
class ValidationResult:
    """Structured result of deterministic financial validation."""

    is_valid: bool
    issues: list[ValidationIssue] = dc.field(default_factory=list)
    metrics: dict[str, Any] = dc.field(default_factory=dict)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def add_issue(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)
        if issue.severity == "error":
            self.is_valid = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "issues": [i.to_dict() for i in self.issues],
            "metrics": self.metrics,
        }
