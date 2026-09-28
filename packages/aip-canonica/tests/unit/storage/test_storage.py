"""Unit tests for configurable document storage and source reference tracking."""

from pathlib import Path

from aip_canonica import (
    BankStatement,
    LocalReferenceStorage,
    SecureRemoteStorage,
    StructuredLocalStorage,
    understand,
)


def test_local_reference_storage(sample_invoice_csv: Path):
    storage = LocalReferenceStorage()
    ref = storage.store(sample_invoice_csv, customer_id="cust_1", account_id="acct_1")

    assert ref.uri == str(sample_invoice_csv)
    assert ref.storage_mode == "reference"
    assert ref.customer_id == "cust_1"
    assert ref.account_id == "acct_1"
    assert "registered_at" in ref.metadata


def test_structured_local_storage(tmp_path: Path, sample_invoice_csv: Path):
    storage_root = tmp_path / "server_storage"
    storage = StructuredLocalStorage(base_dir=storage_root)

    ref = storage.store(
        sample_invoice_csv,
        customer_id="cust_corp_42",
        account_id="acct_savings_99",
    )

    dest_file = Path(ref.uri)
    assert dest_file.exists()
    assert dest_file.name.endswith("sample_invoice.csv")
    assert "cust_corp_42" in str(dest_file)
    assert "acct_savings_99" in str(dest_file)
    assert ref.storage_mode == "structured_server"
    assert ref.metadata["file_size_bytes"] > 0
    assert len(ref.metadata["sha256"]) == 64


def test_secure_remote_storage(sample_invoice_csv: Path):
    storage = SecureRemoteStorage(base_url="sftp://vault.corp.internal/statements")
    ref = storage.store(
        sample_invoice_csv,
        customer_id="enterprise_client",
        account_id="treasury_account",
    )

    assert ref.storage_mode == "secure_remote"
    assert ref.uri.startswith("sftp://vault.corp.internal/statements/enterprise_client/treasury_account/")
    assert "?token=" in ref.uri
    assert ref.metadata["revokable"] is True
    assert ref.metadata["storage_backend"] == "sftp_secure_vault"


def test_understand_with_structured_storage(tmp_path: Path, icici_statement_path: Path):
    storage = StructuredLocalStorage(base_dir=tmp_path / "vault")
    doc = understand(
        icici_statement_path,
        storage=storage,
        customer_id="acme_corp",
        account_id="primary_checking",
    )

    assert isinstance(doc, BankStatement)
    assert doc.provenance is not None
    # Source points to the structured server path
    assert "acme_corp" in doc.provenance.source
    assert "primary_checking" in doc.provenance.source
    assert Path(doc.provenance.source).exists()

    # Provenance metadata contains full storage audit trail
    assert "storage_reference" in doc.provenance.metadata
    storage_meta = doc.provenance.metadata["storage_reference"]
    assert storage_meta["storage_mode"] == "structured_server"
    assert storage_meta["customer_id"] == "acme_corp"
    assert storage_meta["account_id"] == "primary_checking"

    # Child transactions also inherit the structured source reference!
    first_txn = doc.transactions[0]
    assert first_txn.provenance is not None
    assert "acme_corp" in first_txn.provenance.source


def test_understand_with_secure_remote_storage(icici_statement_path: Path):
    storage = SecureRemoteStorage(base_url="https://secure-vault.acme.com/docs")
    doc = understand(
        icici_statement_path,
        storage=storage,
        customer_id="cust_999",
        account_id="acct_888",
    )

    assert isinstance(doc, BankStatement)
    assert doc.provenance is not None
    # Source is the secure remote revokable URL
    assert doc.provenance.source.startswith("https://secure-vault.acme.com/docs/cust_999/acct_888/")
    assert "?token=" in doc.provenance.source

    # Child transactions have the revokable URL reference
    assert doc.transactions[0].provenance.source == doc.provenance.source
