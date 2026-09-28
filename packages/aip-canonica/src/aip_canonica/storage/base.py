"""Base abstractions for document source reference and physical storage management."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class StoredDocumentReference:
    """Represents a stored or referenced document and its tracking metadata."""

    uri: str
    storage_mode: str  # "reference", "structured_server", "secure_remote"
    original_path: str
    customer_id: str | None = None
    account_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = {
            "uri": self.uri,
            "storage_mode": self.storage_mode,
            "original_path": self.original_path,
            "customer_id": self.customer_id,
            "account_id": self.account_id,
            "metadata": dict(self.metadata),
        }
        for k, v in self.metadata.items():
            if k not in data:
                data[k] = v
        return data


@runtime_checkable
class SourceStorage(Protocol):
    """Protocol for storing document files and resolving their provenance references."""

    @property
    def storage_mode(self) -> str:
        """Name of the storage mode."""
        ...

    def store(
        self,
        source_path: Path | str,
        *,
        customer_id: str | None = None,
        account_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoredDocumentReference:
        """Store the document or register its reference, returning a StoredDocumentReference."""
        ...
