"""Unit tests for BankStatement and Transaction canonical models."""

from decimal import Decimal
from aip_canonica.models.bank_statement import BankStatement, Transaction
from aip_canonica.models.base import DatePeriod, TransactionDirection
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models.party import Account, Party
from aip_canonica.models.provenance import Provenance


def test_transaction_creation_and_defaults():
    """Test Transaction model initialization and default properties."""
    txn = Transaction(
        id="txn:1",
        date="2026-05-01",
        amount=Decimal("1500.00"),
        direction=TransactionDirection.CREDIT,
        narration="Client payment",
        balance=Decimal("51500.00"),
        reference="REF123",
        counterparty=Party(id="party:client", name="Client Co"),
    )
    assert txn.id == "txn:1"
    assert txn.amount == Decimal("1500.00")
    assert txn.direction == TransactionDirection.CREDIT
    assert txn.node_type == "Transaction"
    assert txn.counterparty is not None
    assert txn.counterparty.name == "Client Co"

    d = txn.to_dict()
    assert d["amount"] == "1500.00"
    assert d["direction"] == "credit"
    assert d["counterparty"]["name"] == "Client Co"


def test_bank_statement_graph_construction():
    """Test BankStatement graph construction with relationships."""
    # Setup test objects
    account = Account(id="acc:1")
    holder = Party(id="party:holder")
    institution = Party(id="party:institution")
    counterparty = Party(id="party:cafe")
    transaction = Transaction(
        id="txn:1",
        date="2026-05-01",
        amount=Decimal("1000.00"),
        direction=TransactionDirection.DEBIT,
        narration="Test transaction",
        counterparty=counterparty,
    )
    statement = BankStatement(
        id="stmt:1",
        account=account,
        holder=holder,
        institution=institution,
        transactions=[transaction],
    )

    # Validate graph construction
    graph = statement.as_graph()
    assert graph.get_node(statement.id) == statement
    assert graph.get_node(account.id) == account
    assert graph.get_node(holder.id) == holder
    assert graph.get_node(institution.id) == institution
    assert graph.get_node(transaction.id) == transaction
    assert graph.get_node(counterparty.id) == counterparty

    # Validate outgoing relationships from statement
    stmt_outgoing = graph.outgoing(statement.id)
    relations = {r.relation: r.target_id for r in stmt_outgoing}
    assert relations["account"] == account.id
    assert relations["holder"] == holder.id
    assert relations["institution"] == institution.id
    assert relations["contains"] == transaction.id

    # Validate outgoing relationship from transaction
    txn_outgoing = graph.outgoing(transaction.id)
    assert len(txn_outgoing) == 1
    assert txn_outgoing[0].relation == "counterparty"
    assert txn_outgoing[0].target_id == counterparty.id

    # Validate incoming relationships
    assert len(graph.incoming(account.id)) == 1
    assert graph.incoming(account.id)[0].source_id == statement.id
    assert len(graph.incoming(counterparty.id)) == 1
    assert graph.incoming(counterparty.id)[0].source_id == transaction.id


def test_bank_statement_validation_via_method():
    """Test BankStatement validation with valid data."""
    stmt = BankStatement(
        id="stmt:1",
        opening_balance=Decimal("1000.00"),
        closing_balance=Decimal("1500.00"),
        transactions=[
            Transaction(
                id="txn:1",
                date="2026-01-01",
                amount=Decimal("500.00"),
                direction=TransactionDirection.CREDIT,
                narration="Deposit",
            )
        ],
    )
    result = stmt.validate()
    assert result.is_valid
    assert len(result.issues) == 0