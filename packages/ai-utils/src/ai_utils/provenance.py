from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai_utils.source_location import SourceLocation


@dataclass(frozen=True, slots=True)
class Provenance:
    """
    Describes the origin of an object, including its source, location, and additional metadata.

    Attributes:
        source (str): The name or identifier of the source system, module, or component that generated the object.
        location (SourceLocation | None): The specific location within the source where the object was created. May be None if not applicable.
        metadata (dict[str, Any]): Additional information or context associated with the object, stored as key-value pairs.
    """

    source: str
    location: SourceLocation | None = None
    metadata: dict[str, Any] = field(default_factory=dict)