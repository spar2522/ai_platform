"""Built-in storage providers for managing document provenance and physical retention."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import shutil
from typing import Any
import uuid

from aip_canonica.storage.base import StoredDocumentReference


class LocalReferenceStorage:
    """Option 1: Reference-only storage.

    Retains the original client path or URL without moving or duplicating the file.
    Ideal for client-managed uploads or remote APIs calling Canonica.
    """

    @property
    def storage_mode(self) -> str:
        return "reference"

    def store(
        self,
        source_path: Path | str,
        *,
        customer_id: str | None = None,
        account_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoredDocumentReference:
        path_str = str(source_path)
        meta = dict(metadata or {})
        meta["registered_at"] = datetime.now(timezone.utc).isoformat()
        return StoredDocumentReference(
            uri=path_str,
            storage_mode=self.storage_mode,
            original_path=path_str,
            customer_id=customer_id,
            account_id=account_id,
            metadata=meta,
        )


class StructuredLocalStorage:
    """Option 2: Structured server-side physical storage.

    Copies the uploaded document into an organized multi-tenant directory structure:
    `{base_dir}/{customer_id}/{account_id}/{timestamp}_{filename}`
    """

    def __init__(self, base_dir: Path | str = "./storage/documents") -> None:
        self.base_dir = Path(base_dir).resolve()

    @property
    def storage_mode(self) -> str:
        return "structured_server"

    def store(
        self,
        source_path: Path | str,
        *,
        customer_id: str | None = None,
        account_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoredDocumentReference:
        src = Path(source_path)
        cust_dir = customer_id or "unassigned_customer"
        acct_dir = account_id or "unassigned_account"

        target_dir = self.base_dir / cust_dir / acct_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        target_filename = f"{timestamp}_{src.name}"
        dest_path = target_dir / target_filename

        # If source is an existing physical file, copy it securely
        file_hash = ""
        file_size = 0
        if src.exists() and src.is_file():
            shutil.copy2(src, dest_path)
            content = dest_path.read_bytes()
            file_hash = hashlib.sha256(content).hexdigest()
            file_size = len(content)

        meta = dict(metadata or {})
        meta.update(
            {
                "stored_at": datetime.now(timezone.utc).isoformat(),
                "file_size_bytes": file_size,
                "sha256": file_hash,
                "server_path": str(dest_path),
            }
        )

        return StoredDocumentReference(
            uri=str(dest_path),
            storage_mode=self.storage_mode,
            original_path=str(source_path),
            customer_id=customer_id,
            account_id=account_id,
            metadata=meta,
        )


class SecureRemoteStorage:
    """Option 3: Secure remote / FTP / SFTP / S3 storage with revokable access URLs.

    Simulates or integrates with a dedicated secure vault/FTP server. Generates a tokenized,
    revokable remote access URL and records security metadata for audit compliance.
    """

    def __init__(
        self,
        base_url: str = "sftp://secure-vault.internal/financial_docs",
        *,
        token_ttl_seconds: int = 86400,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token_ttl_seconds = token_ttl_seconds

    @property
    def storage_mode(self) -> str:
        return "secure_remote"

    def store(
        self,
        source_path: Path | str,
        *,
        customer_id: str | None = None,
        account_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoredDocumentReference:
        src = Path(source_path)
        cust_seg = customer_id or "cust_default"
        acct_seg = account_id or "acct_default"
        access_token = uuid.uuid4().hex
        doc_id = uuid.uuid4().hex[:12]

        # Secure remote URL with access token for access control / revocation
        remote_url = f"{self.base_url}/{cust_seg}/{acct_seg}/{doc_id}/{src.name}?token={access_token}"

        meta = dict(metadata or {})
        meta.update(
            {
                "stored_at": datetime.now(timezone.utc).isoformat(),
                "access_token": access_token,
                "token_ttl_seconds": self.token_ttl_seconds,
                "revokable": True,
                "storage_backend": "sftp_secure_vault",
            }
        )

        return StoredDocumentReference(
            uri=remote_url,
            storage_mode=self.storage_mode,
            original_path=str(source_path),
            customer_id=customer_id,
            account_id=account_id,
            metadata=meta,
        )
