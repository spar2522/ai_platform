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
        field: The specific field or location where the issue occurred (optional).
        details: Additional contextual information about the issue (optional).
    """

    severity: Literal["error", "warning"]
    code: str
    message: str
    field: str | None = None
    details: dict[str, Any] = dc.field(default_factory=dict)

    def __post_init__(self):
        """Validate that severity is one of the allowed values."""
        if self.severity not in ["error", "warning"]:
            raise ValueError("Severity must be 'error' or 'warning'")

    def to_dict(self) -> dict[str, Any]:
        """Convert the ValidationIssue instance to a dictionary representation."""
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


# Alias for backward compatibility or alternative naming
Finding = ValidationIssue


@dc.dataclass(slots=True)
class ValidationResult:
    """Structured result of deterministic financial validation.

    Attributes:
        is_valid: Whether the validation passed without errors.
        issues: A list of ValidationIssue instances.
        metrics: Additional metrics or statistics from the validation process.
    """

    is_valid: bool
    issues: list[ValidationIssue] = dc.field(default_factory=list)
    metrics: dict[str, Any] = dc.field(default_factory=dict)

    @property
    def errors(self) -> list[ValidationIssue]:
        """Return all issues with severity 'error'."""
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Return all issues with severity 'warning'."""
        return [i for i in self.issues if i.severity == "warning"]

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add a validation issue to the result.

        If the issue is an error, the 'is_valid' flag is set to False.
        """
        self.issues.append(issue)
        if issue.severity == "error":
            self.is_valid = False

    def to_dict(self) -> dict[str, Any]:
        """Convert the ValidationResult instance to a dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "issues": [i.to_dict() for i in self.issues],
            "metrics": self.metrics,
        }