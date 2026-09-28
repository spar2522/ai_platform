"""Unit tests for BankStatement and Transaction canonical models."""

from decimal import Decimal
from aip_canonica.models.bank_statement import BankStatement, Transaction
from aip_canonica.models.base import DatePeriod, TransactionDirection
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models.party import Account, Party
from aip_canonica.models.provenance import Provenance


def test_transaction_creation_and_defaults():
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
    account = Account(id="acc:123", account_number="1234567890", ifsc_code="ICIC0001")
    holder = Party(id="party:holder", name="John Doe")
    institution = Party(id="party:bank", name="ICICI Bank")
    txn = Transaction(
        id="txn:1",
        date="2026-05-01",
        amount=Decimal("1000.00"),
        direction=TransactionDirection.DEBIT,
        narration="Coffee Shop payment",
        counterparty=Party(id="party:cafe", name="Coffee Shop"),
    )

    stmt = BankStatement(
        id="stmt:1",
        account=account,
        holder=holder,
        institution=institution,
        period=DatePeriod(start_date="2026-05-01", end_date="2026-05-31"),
        opening_balance=Decimal("10000.00"),
        closing_balance=Decimal("9000.00"),
        transactions=[txn],
        provenance=Provenance(source="statement.xlsx", sheet="Sheet0"),
    )

    assert stmt.document_type == DocumentType.BANK_STATEMENT
    assert stmt.node_type == "BankStatement"

    graph = stmt.as_graph()
    assert graph.get_node(stmt.id) == stmt
    assert graph.get_node(account.id) == account
    assert graph.get_node(holder.id) == holder
    assert graph.get_node(institution.id) == institution
    assert graph.get_node(txn.id) == txn
    assert graph.get_node("party:cafe") is not None

    # Outgoing relationships from statement
    stmt_outgoing = graph.outgoing(stmt.id)
    relations = {r.relation: r.target_id for r in stmt_outgoing}
    assert relations["account"] == "acc:123"
    assert relations["holder"] == "party:holder"
    assert relations["institution"] == "party:bank"
    assert relations["contains"] == "txn:1"

    # Outgoing relationship from transaction to counterparty
    txn_outgoing = graph.outgoing(txn.id)
    assert len(txn_outgoing) == 1
    assert txn_outgoing[0].relation == "counterparty"
    assert txn_outgoing[0].target_id == "party:cafe"

    # Incoming relationship discovery
    assert len(graph.incoming(account.id)) == 1
    assert graph.incoming(account.id)[0].source_id == stmt.id
    assert len(graph.incoming("party:cafe")) == 1
    assert graph.incoming("party:cafe")[0].source_id == txn.id


def test_bank_statement_validation_via_method():
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
