"""Party and Account entities participating in canonical financial graphs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aip_canonica.models.provenance import Provenance


@dataclass(frozen=True, slots=True)
class Party:
    """An individual, business entity, or financial institution."""

    id: str
    name: str
    tax_id: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    provenance: Provenance | None = None

    @property
    def node_type(self) -> str:
        return "Party"

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "node_type": self.node_type,
            "name": self.name,
        }
        if self.tax_id is not None:
            data["tax_id"] = self.tax_id
        if self.address is not None:
            data["address"] = self.address
        if self.phone is not None:
            data["phone"] = self.phone
        if self.email is not None:
            data["email"] = self.email
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        return data


@dataclass(frozen=True, slots=True)
class Account:
    """A financial account (bank account, ledger account, wallet)."""

    id: str
    account_number: str
    account_type: str | None = None
    institution_name: str | None = None
    ifsc_code: str | None = None
    currency: str = "INR"
    holder_id: str | None = None
    provenance: Provenance | None = None

    @property
    def node_type(self) -> str:
        return "Account"

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "node_type": self.node_type,
            "account_number": self.account_number,
            "currency": self.currency,
        }
        if self.account_type is not None:
            data["account_type"] = self.account_type
        if self.institution_name is not None:
            data["institution_name"] = self.institution_name
        if self.ifsc_code is not None:
            data["ifsc_code"] = self.ifsc_code
        if self.holder_id is not None:
            data["holder_id"] = self.holder_id
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        return data
