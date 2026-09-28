"""Tabular invoice extractor converting invoice documents (CSV or Excel) into canonical Invoice models."""

from __future__ import annotations

from decimal import Decimal
import re

from aip_canonica.extractors.helpers import normalize_text, parse_decimal
from aip_canonica.models import Workbook
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models.invoice import Discount, Invoice, InvoiceLine, Tax
from aip_canonica.models.party import Party
from aip_canonica.models.provenance import Provenance


class TabularInvoiceExtractor:
    """Deterministic extractor for tabular invoice documents."""

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.INVOICE

    @property
    def name(self) -> str:
        return "tabular_invoice"

    @property
    def is_generic(self) -> bool:
        return True

    def matches(self, workbook: Workbook) -> bool:
        for sheet in workbook.sheets:
            has_invoice_keyword = False
            has_table_cols = False
            for row in sheet.rows[:30]:
                texts = [normalize_text(c.value) for c in row.cells if c.value is not None]
                joined = " ".join(texts)
                if any(k in joined for k in ["invoice", "tax invoice", "bill to", "invoice no", "inv no"]):
                    has_invoice_keyword = True

                has_item = any(any(k in t for k in ["item", "description", "particular", "product"]) for t in texts)
                has_amt = any(any(k in t for k in ["amount", "total", "rate", "price", "subtotal"]) for t in texts)
                if has_item and has_amt:
                    has_table_cols = True

            if has_invoice_keyword and has_table_cols:
                return True
        return False

    def extract(self, workbook: Workbook, *, source_name: str = "") -> Invoice:
        target_sheet = None
        header_row_idx = None
        col_map: dict[str, int] = {}

        for sheet in workbook.sheets:
            for row in sheet.rows[:30]:
                texts = [normalize_text(c.value) for c in row.cells]
                has_item = any(any(k in t for k in ["item", "description", "particular", "product"]) for t in texts)
                has_amt = any(any(k in t for k in ["amount", "total", "line total", "price"]) for t in texts)

                if has_item and has_amt:
                    header_row_idx = row.index
                    target_sheet = sheet
                    for c_idx, cell in enumerate(row.cells):
                        txt = normalize_text(cell.value)
                        if any(k in txt for k in ["item", "description", "particular", "product"]):
                            col_map["description"] = c_idx
                        elif any(k in txt for k in ["qty", "quantity"]):
                            col_map["quantity"] = c_idx
                        elif any(k in txt for k in ["rate", "unit price", "price"]):
                            col_map["unit_price"] = c_idx
                        elif any(k in txt for k in ["line total", "amount", "total"]):
                            col_map["amount"] = c_idx
                        elif any(k in txt for k in ["hsn", "sac"]):
                            col_map["hsn_sac"] = c_idx
                        elif "tax" in txt or "gst" in txt:
                            col_map["tax"] = c_idx
                    break
            if header_row_idx is not None:
                break

        if target_sheet is None or header_row_idx is None:
            raise ValueError("Could not find tabular invoice line items header.")

        # Metadata search before the line items table
        invoice_number = None
        invoice_date = None
        due_date = None
        issuer_name = None
        recipient_name = None
        issuer_tax_id = None
        recipient_tax_id = None

        for row in target_sheet.rows:
            if row.index >= header_row_idx:
                break
            for c_idx, cell in enumerate(row.cells):
                raw_cell = str(cell.value or "").strip()
                if not raw_cell:
                    continue
                txt = normalize_text(raw_cell)
                next_val = str(row.cells[c_idx + 1].value or "").strip() if c_idx + 1 < len(row.cells) else ""
                
                # Check for colon in same cell
                cand_val = ""
                if ":" in raw_cell:
                    parts = raw_cell.split(":", 1)
                    key_part = normalize_text(parts[0])
                    val_part = parts[1].strip()
                    if val_part:
                        cand_val = val_part
                else:
                    key_part = txt
                
                final_val = cand_val or next_val
                if not final_val:
                    continue

                if any(k in key_part for k in ["invoice number", "invoice no", "invoice #", "inv no", "bill no"]) and not invoice_number:
                    invoice_number = final_val
                elif any(k in key_part for k in ["invoice date", "date"]) and "due" not in key_part and not invoice_date:
                    invoice_date = final_val
                elif "due date" in key_part and not due_date:
                    due_date = final_val
                elif any(k in key_part for k in ["from", "issuer", "seller", "supplier"]) and not issuer_name:
                    issuer_name = final_val
                elif any(k in key_part for k in ["bill to", "customer", "recipient", "buyer"]) and not recipient_name:
                    recipient_name = final_val
                elif "gstin" in key_part:
                    if issuer_tax_id is None:
                        issuer_tax_id = final_val
                    elif recipient_tax_id is None:
                        recipient_tax_id = final_val

        # Line items extraction
        lines: list[InvoiceLine] = []
        subtotal: Decimal | None = None
        tax_total: Decimal | None = None
        discount_total: Decimal | None = None
        total_amount: Decimal | None = None

        for row in target_sheet.rows:
            if row.index <= header_row_idx:
                continue

            first_val = normalize_text(row.cells[0].value if row.cells else "")
            # Check for footer / summary rows
            if any(k in first_val for k in ["subtotal", "sub total", "total", "tax", "gst", "discount"]):
                for c_idx, cell in enumerate(row.cells):
                    txt = normalize_text(cell.value)
                    val = parse_decimal(row.cells[c_idx + 1].value) if c_idx + 1 < len(row.cells) else None
                    if val is not None:
                        if "subtotal" in txt or "sub total" in txt:
                            subtotal = val
                        elif "tax" in txt or "gst" in txt:
                            tax_total = val
                        elif "discount" in txt:
                            discount_total = val
                        elif "total" in txt and "sub" not in txt and total_amount is None:
                            total_amount = val
                continue

            # Check if row is empty
            if not any(c.value is not None and str(c.value).strip() != "" for c in row.cells):
                continue

            def get_val(key: str) -> str:
                idx = col_map.get(key)
                if idx is not None and idx < len(row.cells):
                    v = row.cells[idx].value
                    return str(v).strip() if v is not None else ""
                return ""

            desc = get_val("description")
            qty_dec = parse_decimal(get_val("quantity"))
            price_dec = parse_decimal(get_val("unit_price"))
            amt_dec = parse_decimal(get_val("amount"))
            hsn = get_val("hsn_sac") or None
            tax_str = get_val("tax")

            if not desc and amt_dec is None:
                continue

            # If amount is missing, calculate qty * price
            if amt_dec is None and qty_dec is not None and price_dec is not None:
                amt_dec = qty_dec * price_dec

            if amt_dec is None:
                continue

            line_tax: Tax | None = None
            tax_val = parse_decimal(tax_str)
            if tax_val is not None:
                line_tax = Tax(
                    id=f"tax:line:{len(lines) + 1}",
                    tax_type="GST",
                    amount=tax_val,
                )

            active_cells = [c.location for c in row.cells if c.value is not None]
            provenance = Provenance.from_cells(
                active_cells,
                source=source_name,
                sheet=target_sheet.name,
                row=row.index,
            )

            lines.append(
                InvoiceLine(
                    id=f"line:{len(lines) + 1}",
                    description=desc,
                    quantity=qty_dec,
                    unit_price=price_dec,
                    amount=amt_dec,
                    tax=line_tax,
                    hsn_sac=hsn,
                    provenance=provenance,
                )
            )

        if subtotal is None and lines:
            subtotal = sum((item.amount for item in lines), Decimal("0"))

        taxes: list[Tax] = []
        if tax_total is not None:
            taxes.append(Tax(id="tax:summary:1", tax_type="GST", amount=tax_total))

        discounts: list[Discount] = []
        if discount_total is not None:
            discounts.append(Discount(id="disc:summary:1", amount=discount_total))

        if total_amount is None:
            total_amount = (subtotal or Decimal("0")) + (tax_total or Decimal("0")) - (discount_total or Decimal("0"))

        issuer: Party | None = None
        if issuer_name or issuer_tax_id:
            issuer_id = f"party:gstin:{issuer_tax_id}" if issuer_tax_id else f"party:{re.sub(r'[^a-zA-Z0-9]+', '_', (issuer_name or 'issuer')).lower()}"
            issuer = Party(id=issuer_id, name=issuer_name or "Issuer", tax_id=issuer_tax_id)

        recipient: Party | None = None
        if recipient_name or recipient_tax_id:
            recip_id = f"party:gstin:{recipient_tax_id}" if recipient_tax_id else f"party:{re.sub(r'[^a-zA-Z0-9]+', '_', (recipient_name or 'recipient')).lower()}"
            recipient = Party(id=recip_id, name=recipient_name or "Recipient", tax_id=recipient_tax_id)

        inv_num = invoice_number or "INV-UNKNOWN"
        return Invoice(
            id=f"inv:{inv_num}",
            invoice_number=inv_num,
            invoice_date=invoice_date or "UNKNOWN",
            due_date=due_date,
            total_amount=total_amount,
            issuer=issuer,
            recipient=recipient,
            subtotal=subtotal,
            tax_total=tax_total,
            discount_total=discount_total,
            lines=lines,
            taxes=taxes,
            discounts=discounts,
            currency="INR",
            provenance=Provenance(source=source_name, sheet=target_sheet.name, metadata={"extractor": self.name}),
        )
