"""Unit tests for InterestCertificate and TDSCertificate canonical models."""

from decimal import Decimal
from aip_canonica.models.certificates import (
    InterestCertificate,
    TDSCertificate,
    TDSEntry,
)
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models.party import Account, Party


def test_interest_certificate_creation_and_graph():
    """Test creation of InterestCertificate and its graph representation."""
    institution_party = Party(id="party:bank", name="HDFC Bank")
    recipient_party = Party(id="party:client", name="Arpit Ratan")
    account = Account(id="acc:1", account_number="5010012345")

    cert = InterestCertificate(
        id="cert:int:2026:1",
        certificate_number="INT-2026-001",
        interest_amount=Decimal("45000.00"),
        tds_deducted=Decimal("4500.00"),
        institution=institution_party,
        recipient=recipient_party,
        account=account,
    )

    assert cert.document_type == DocumentType.INTEREST_CERTIFICATE
    assert cert.node_type == "InterestCertificate"

    graph = cert.as_graph()
    assert graph.get_node(cert.id) == cert
    assert graph.get_node(institution_party.id) == institution_party
    assert graph.get_node(recipient_party.id) == recipient_party
    assert graph.get_node(account.id) == account

    validation_result = cert.validate()
    assert validation_result.is_valid
    assert len(validation_result.issues) == 0


def test_interest_certificate_validation_negative_interest():
    """Test validation failure for negative interest amount."""
    cert = InterestCertificate(
        id="cert:bad",
        interest_amount=Decimal("-100.00"),
    )
    validation_result = cert.validate()
    assert not validation_result.is_valid
    assert any(i.code == "NEGATIVE_INTEREST" for i in validation_result.errors)


def test_tds_certificate_creation_and_graph():
    """Test creation of TDSCertificate and its graph representation."""
    deductor_party = Party(id="party:corp", name="Employer Corp", tax_id="BLRP12345F")
    deductee_party = Party(id="party:emp", name="Employee", tax_id="ABCDE1234F")

    tds_entry_q1 = TDSEntry(
        id="tds:q1",
        section="192",
        amount_paid=Decimal("250000.00"),
        tds_amount=Decimal("25000.00"),
        date_paid="2026-06-30",
    )
    tds_entry_q2 = TDSEntry(
        id="tds:q2",
        section="192",
        amount_paid=Decimal("250000.00"),
        tds_amount=Decimal("25000.00"),
        date_paid="2026-07-01",
    )

    tds_cert = TDSCertificate(
        id="tds:valid",
        certificate_number="TDS-VALID",
        total_amount_paid=Decimal("500000.00"),
        total_tds_amount=Decimal("50000.00"),
        deductor=deductor_party,
        deductee=deductee_party,
        entries=[tds_entry_q1, tds_entry_q2],
    )

    assert tds_cert.document_type == DocumentType.TDS_CERTIFICATE
    assert tds_cert.node_type == "TDSCertificate"

    graph = tds_cert.as_graph()
    assert graph.get_node(tds_cert.id) == tds_cert
    assert graph.get_node(deductor_party.id) == deductor_party
    assert graph.get_node(deductee_party.id) == deductee_party
    assert graph.get_node(tds_entry_q1.id) == tds_entry_q1
    assert graph.get_node(tds_entry_q2.id) == tds_entry_q2

    validation_result = tds_cert.validate()
    assert validation_result.is_valid


def test_tds_certificate_validation_mismatch():
    """Test validation failure for mismatch between entry and certificate totals."""
    tds_cert = TDSCertificate(
        id="tds:bad",
        certificate_number="TDS-BAD",
        total_amount_paid=Decimal("500000.00"),
        total_tds_amount=Decimal("50000.00"),
        entries=[
            TDSEntry(
                id="t1",
                amount_paid=Decimal("100000.00"),
                tds_amount=Decimal("10000.00"),
            )
        ],
    )
    validation_result = tds_cert.validate()
    assert not validation_result.is_valid
    assert any(i.code == "TDS_SUM_MISMATCH" for i in validation_result.errors)