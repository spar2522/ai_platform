"""Unit tests for Invoice canonical domain models."""

from decimal import Decimal
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models.invoice import Discount, Invoice, InvoiceLine, Tax
from aip_canonica.models.party import Party


def test_invoice_creation_and_graph():
    """Test creation of Invoice and its graph relationships."""
    # Setup parties
    issuer = Party(id="party:issuer", name="Vendor Inc", tax_id="29ABCDE1234F1Z5")
    recipient = Party(id="party:buyer", name="Buyer Corp", tax_id="27XYZAB9876C1Z2")

    # Setup invoice line and taxes
    line_tax = Tax(id="tax:line:1", tax_type="CGST", amount=Decimal("90.00"), rate=Decimal("9"))
    line1 = InvoiceLine(
        id="line:1",
        description="Widget A",
        quantity=Decimal("10"),
        unit_price=Decimal("100.00"),
        amount=Decimal("1000.00"),
        tax=line_tax,
    )
    summary_tax = Tax(id="tax:summary:1", tax_type="IGST", amount=Decimal("180.00"), rate=Decimal("18"))
    discount = Discount(id="disc:1", description="Early payment", amount=Decimal("50.00"))

    # Setup invoice
    inv = Invoice(
        id="inv:1001",
        invoice_number="INV-1001",
        invoice_date="2026-05-10",
        total_amount=Decimal("1130.00"),
        issuer=issuer,
        recipient=recipient,
        subtotal=Decimal("1000.00"),
        lines=[line1],
        taxes=[summary_tax],
        discounts=[discount],
    )

    # Verify basic invoice properties
    assert inv.id == "inv:1001"
    assert inv.invoice_number == "INV-1001"
    assert inv.total_amount == Decimal("1130.00")
    assert len(inv.lines) == 1
    assert len(inv.taxes) == 1
    assert len(inv.discounts) == 1

    # Verify graph node presence
    graph_nodes = [issuer, recipient, line1, line_tax, summary_tax, discount, inv]
    for node in graph_nodes:
        assert node in inv.graph.nodes, f"Node {node} not found in graph"

    # Verify graph relationships
    outgoing_relations_from_invoice = inv.graph.outgoing_edges(inv)
    relations_map = {edge[1]: edge[2] for edge in outgoing_relations_from_invoice}
    assert relations_map["line:1"] == line1
    assert relations_map["tax:line:1"] == line_tax
    assert relations_map["tax:summary:1"] == summary_tax
    assert relations_map["disc:1"] == discount

    # Verify reverse relationships
    assert inv.graph.incoming_edges(issuer)[0][0] == inv
    assert inv.graph.incoming_edges(recipient)[0][0] == inv
    assert inv.graph.incoming_edges(line1)[0][0] == inv
    assert inv.graph.incoming_edges(line_tax)[0][0] == inv
    assert inv.graph.incoming_edges(summary_tax)[0][0] == inv
    assert inv.graph.incoming_edges(discount)[0][0] == inv


def test_invoice_validation():
    """Test validation of an invoice with valid data."""
    # Setup invoice with valid data
    inv = Invoice(
        id="inv:2001",
        invoice_number="INV-2001",
        invoice_date="2023-01-01",
        total_amount=Decimal("1050.00"),
        issuer=Party(id="party:valid", name="Valid Issuer"),
        recipient=Party(id="party:valid", name="Valid Recipient"),
        subtotal=Decimal("1000.00"),
        lines=[
            InvoiceLine(
                id="line:2",
                description="Valid Item",
                quantity=Decimal("1"),
                unit_price=Decimal("1000.00"),
                amount=Decimal("1000.00"),
            )
        ],
        taxes=[Tax(id="tax:2", tax_type="GST", amount=Decimal("100.00"), rate=Decimal("10"))],
        discounts=[Discount(id="disc:2", amount=Decimal("50.00"))],
    )

    # Validate invoice
    result = inv.validate()
    assert result.is_valid, "Validation should pass for valid invoice"
    assert len(result.issues) == 0, "No validation issues should be present"