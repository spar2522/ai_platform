"""Unit tests for CanonicalGraph and Relationship models."""

from aip_canonica.models.graph import CanonicalGraph, Relationship
from aip_canonica.models.party import Account, Party


def test_relationship_creation_and_serialization():
    rel = Relationship(
        source_id="inv:1",
        relation="issuer",
        target_id="party:acme",
        target_type="Party",
        properties={"role": "supplier"},
    )
    assert rel.source_id == "inv:1"
    assert rel.relation == "issuer"
    assert rel.target_id == "party:acme"
    assert rel.target_type == "Party"
    assert rel.properties == {"role": "supplier"}

    d = rel.to_dict()
    assert d["source_id"] == "inv:1"
    assert d["relation"] == "issuer"
    assert d["target_id"] == "party:acme"
    assert d["target_type"] == "Party"
    assert d["properties"]["role"] == "supplier"


def test_adding_and_retrieving_nodes():
    graph = CanonicalGraph()
    party = Party(id="party:1", name="Acme Corp")
    graph.add_node(party)

    assert graph.get_node("party:1") == party
    assert graph.get_node("party:unknown") is None
    assert len(graph.nodes) == 1


def test_outgoing_relationship_traversal():
    graph = CanonicalGraph()
    party = Party(id="party:1", name="Acme Corp")
    account = Account(id="acc:1", account_number="12345", holder_id="party:1")

    graph.add_node(party)
    graph.add_node(account)

    rel = Relationship(source_id="acc:1", relation="holder", target_id="party:1", target_type="Party")
    graph.add_relationship(rel)

    outgoing = graph.outgoing("acc:1")
    assert len(outgoing) == 1
    assert outgoing[0].target_id == "party:1"

    outgoing_filtered = graph.outgoing("acc:1", relation="holder")
    assert len(outgoing_filtered) == 1

    outgoing_none = graph.outgoing("acc:1", relation="contains")
    assert len(outgoing_none) == 0


def test_incoming_relationship_traversal():
    graph = CanonicalGraph()
    party = Party(id="party:1", name="Acme Corp")
    account = Account(id="acc:1", account_number="12345", holder_id="party:1")

    graph.add_node(party)
    graph.add_node(account)

    rel = Relationship(source_id="acc:1", relation="holder", target_id="party:1", target_type="Party")
    graph.add_relationship(rel)

    incoming = graph.incoming("party:1")
    assert len(incoming) == 1
    assert incoming[0].source_id == "acc:1"
    assert incoming[0].relation == "holder"


def test_relationship_traversal_with_missing_targets():
    graph = CanonicalGraph()
    account = Account(id="acc:1", account_number="12345")
    graph.add_node(account)

    missing_rel = Relationship(source_id="acc:1", relation="holder", target_id="party:missing", target_type="Party")
    graph.add_relationship(missing_rel)

    targets = graph.target_nodes("acc:1", "holder")
    assert len(targets) == 0

    assert len(graph.outgoing("acc:1")) == 1
    assert graph.outgoing("acc:1")[0].target_id == "party:missing"


def test_graph_serialization():
    graph = CanonicalGraph()
    party = Party(id="party:1", name="Acme")
    graph.add_node(party)
    graph.add_relationship(Relationship(source_id="doc:1", relation="issuer", target_id="party:1"))

    data = graph.to_dict()
    assert "nodes" in data
    assert "relationships" in data
    assert len(data["nodes"]) == 1
    assert len(data["relationships"]) == 1
    assert data["nodes"][0]["id"] == "party:1"
    assert data["nodes"][0]["name"] == "Acme"
    assert data["relationships"][0]["source_id"] == "doc:1"
    assert data["relationships"][0]["relation"] == "issuer"
    assert data["relationships"][0]["target_id"] == "party:1"
    assert data["relationships"][0]["target_type"] == "Party"