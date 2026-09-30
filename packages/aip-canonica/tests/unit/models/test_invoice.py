"""Unit tests for Invoice canonical domain models."""

from decimal import Decimal
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models.invoice import Discount, Invoice, InvoiceLine, Tax
from aip_canonica.models.party import Party


def test_invoice_creation_and_graph():
    # Create parties involved in the invoice
    issuer = Party(id="party:issuer", name="Vendor Inc", tax_id="29ABCDE1234F1Z5")
    recipient = Party(id="party:buyer", name="Buyer Corp", tax_id="27XYZAB9876C1Z2")

    # Define tax for the invoice line
    line_tax = Tax(id="tax:line:1", tax_type="CGST", amount=Decimal("90.00"), rate=Decimal("9"))
    # Create an invoice line with quantity, unit price, and tax
    line1 = InvoiceLine(
        id="line:1",
        description="Widget A",
        quantity=Decimal("10"),
        unit_price=Decimal("100.00"),
        amount=Decimal("1000.00"),
        tax=line_tax,
    )

    # Define summary tax for the invoice
    summary_tax = Tax(id="tax:summary:1", tax_type="IGST", amount=Decimal("180.00"), rate=Decimal("18"))
    # Define a discount for the invoice
    discount = Discount(id="disc:1", description="Early payment", amount=Decimal("50.00"))

    # Construct the invoice with all components
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

    # Verify invoice metadata
    assert inv.document_type == DocumentType.INVOICE
    assert inv.node_type == "Invoice"
    assert len(inv.lines) == 1

    # Generate graph representation of the invoice
    graph = inv.as_graph()

    # Ensure all nodes are correctly represented in the graph
    assert graph.get_node(inv.id) == inv
    assert graph.get_node(issuer.id) == issuer
    assert graph.get_node(recipient.id) == recipient
    assert graph.get_node(line1.id) == line1
    assert graph.get_node(line_tax.id) == line_tax
    assert graph.get_node(summary_tax.id) == summary_tax
    assert graph.get_node(discount.id) == discount

    # Check relationships from the invoice node
    outgoing_inv = graph.outgoing(inv.id)
    relations = {r.relation: r.target_id for r in outgoing_inv}
    assert relations["issuer"] == issuer.id
    assert relations["recipient"] == recipient.id
    assert relations["contains"] == line1.id

    # Check relationship from the invoice line to its tax
    line_outgoing = graph.outgoing(line1.id)
    assert len(line_outgoing) == 1
    assert line_outgoing[0].relation == "tax"
    assert line_outgoing[0].target_id == line_tax.id

    # Verify incoming relationships for issuer and recipient
    assert len(graph.incoming(issuer.id)) == 1
    assert graph.incoming(issuer.id)[0].source_id == inv.id
    assert len(graph.incoming(recipient.id)) == 1
    assert graph.incoming(recipient.id)[0].source_id == inv.id


def test_invoice_validation():
    # Construct a valid invoice
    inv = Invoice(
        id="inv:1",
        invoice_number="INV-1",
        invoice_date="2026-01-01",
        total_amount=Decimal("1050.00"),
        subtotal=Decimal("1000.00"),
        lines=[InvoiceLine(id="line:1", description="Item", amount=Decimal("1000.00"))],
        taxes=[Tax(id="tax:1", tax_type="GST", amount=Decimal("100.00"))],
        discounts=[Discount(id="disc:1", amount=Decimal("50.00"))],
    )

    # Validate the invoice and ensure no issues are found
    result = inv.validate()
    assert result.is_valid
    assert len(result.issues) == 0