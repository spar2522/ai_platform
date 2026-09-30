"""Unit tests for Ledger and LedgerEntry canonical models."""

from decimal import Decimal
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models.ledger import EntryDirection, Ledger, LedgerEntry
from aip_canonica.models.party import Account, Party


def test_ledger_creation_and_graph():
    account = Account(id="acc:sales", account_number="Sales Account")
    party = Party(id="party:cust", name="Customer A")
    counterparty = Party(id="party:cp", name="Supplier B")

    entry_opening = LedgerEntry(
        id="entry:1",
        date="2026-04-01",
        narration="Opening entry",
        amount=Decimal("5000.00"),
        direction=EntryDirection.DEBIT,
        counterparty=counterparty,
    )

    sales_ledger = Ledger(
        id="ledger:sales",
        name="Sales Ledger",
        account=account,
        party=party,
        opening_balance=Decimal("0.00"),
        closing_balance=Decimal("5000.00"),
        entries=[entry_opening],
    )

    assert sales_ledger.document_type == DocumentType.LEDGER
    assert sales_ledger.node_type == "Ledger"

    graph = sales_ledger.as_graph()
    assert graph.get_node(sales_ledger.id) == sales_ledger
    assert graph.get_node(account.id) == account
    assert graph.get_node(party.id) == party
    assert graph.get_node(entry_opening.id) == entry_opening
    assert graph.get_node(counterparty.id) == counterparty

    # Outgoing relationships from the ledger
    outgoing_relations = {r.relation: r.target_id for r in graph.outgoing(sales_ledger.id)}
    assert outgoing_relations["account"] == account.id
    assert outgoing_relations["party"] == party.id
    assert outgoing_relations["contains"] == entry_opening.id

    # Relationship from entry to counterparty
    entry_relations = graph.outgoing(entry_opening.id)
    assert len(entry_relations) == 1
    assert entry_relations[0].relation == "counterparty"
    assert entry_relations[0].target_id == counterparty.id

    # Incoming relationships to account and party
    assert len(graph.incoming(account.id)) == 1
    assert graph.incoming(account.id)[0].source_id == sales_ledger.id
    assert len(graph.incoming(party.id)) == 1
    assert graph.incoming(party.id)[0].source_id == sales_ledger.id


def test_ledger_validation():
    test_ledger = Ledger(
        id="ledger:test",
        name="Test",
        opening_balance=Decimal("1000.00"),
        closing_balance=Decimal("2500.00"),
        entries=[
            LedgerEntry(
                id="e1",
                date="2026-01-01",
                narration="d1",
                amount=Decimal("2000.00"),
                direction=EntryDirection.DEBIT,
            ),
            LedgerEntry(
                id="e2",
                date="2026-01-02",
                narration="c1",
                amount=Decimal("500.00"),
                direction=EntryDirection.CREDIT,
            ),
        ],
    )
    result = test_ledger.validate()
    assert result.is_valid
    assert len(result.issues) == 0