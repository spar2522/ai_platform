from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai_utils.source_location import SourceLocation


@dataclass(frozen=True, slots=True)
class Provenance:
    """
    Describes where an object originated.
    """

    source: str

    location: SourceLocation | None = None

    metadata: dict[str, Any] = field(default_factory=dict)
