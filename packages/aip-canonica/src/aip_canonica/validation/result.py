"""Validation result data structures."""

from __future__ import annotations

import dataclasses as dc
from typing import Any, Literal

Severity = Literal["error", "warning"]


@dc.dataclass(frozen=True, slots=True)
class ValidationIssue:
    """A single issue discovered during deterministic financial validation.

    Attributes:
        severity: The severity level of the issue ("error" or "warning").
        code: A unique identifier for the type of issue.
        message: A human-readable description of the issue.
        field: Optional field name associated with the issue.
        details: Additional context or data related to the issue.
    """

    severity: Literal["error", "warning"]
    code: str
    message: str
    field: str | None = None
    details: dict[str, Any] = dc.field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the validation issue to a dictionary representation."""
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


Finding = ValidationIssue  # Alias for backward compatibility or alternative naming


@dc.dataclass(slots=True)
class ValidationResult:
    """Structured result of deterministic financial validation.

    Attributes:
        is_valid: A flag indicating whether the validation passed.
        issues: A list of validation issues discovered.
        metrics: Additional metrics or statistics from the validation process.

    Note:
        The `is_valid` flag is automatically updated when using `add_issue`.
        Direct modification of the `issues` list may result in inconsistencies
        with `is_valid` if not done through `add_issue`.
    """

    is_valid: bool
    issues: list[ValidationIssue] = dc.field(default_factory=list)
    metrics: dict[str, Any] = dc.field(default_factory=dict)

    @property
    def errors(self) -> list[ValidationIssue]:
        """Return a list of all error-level validation issues."""
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Return a list of all warning-level validation issues."""
        return [i for i in self.issues if i.severity == "warning"]

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add a validation issue to the result and update the validity status."""
        self.issues.append(issue)
        if issue.severity == "error":
            self.is_valid = False

    def to_dict(self) -> dict[str, Any]:
        """Convert the validation result to a dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "issues": [i.to_dict() for i in self.issues],
            "metrics": self.metrics,
        }