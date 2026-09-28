"""Deterministic extractor for ICICI Bank statement layouts."""

from __future__ import annotations

from decimal import Decimal
import re

from aip_canonica.extractors.helpers import (
    extract_counterparty_from_narration,
    normalize_text,
    parse_decimal,
)
from aip_canonica.models.bank_statement import BankStatement, Transaction
from aip_canonica.models.base import DatePeriod, TransactionDirection
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models.party import Account, Party
from aip_canonica.models.provenance import Provenance
from aip_canonica.models import Workbook


class ICICIBankStatementExtractor:
    """Extractor for ICICI Bank detailed account statements."""

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.BANK_STATEMENT

    @property
    def name(self) -> str:
        return "icici_bank_statement"

    @property
    def is_generic(self) -> bool:
        return False

    def matches(self, workbook: Workbook) -> bool:
        """Anchor-based matching: checks for ICICI statement header tokens."""
        for sheet in workbook.sheets:
            for row in sheet.rows[:40]:
                row_texts = [normalize_text(c.value) for c in row.cells if c.value is not None]
                joined = " ".join(row_texts)
                # Check for structural table headers
                has_tran_id = any("tran. id" in t or "tran id" in t for t in row_texts)
                has_withdrawal = any("withdrawal amt" in t for t in row_texts)
                has_deposit = any("deposit amt" in t for t in row_texts)
                if has_tran_id and (has_withdrawal or has_deposit):
                    return True
                # Or ICICI header with account details
                if "icici bank" in joined and "detailed statement" in joined:
                    return True
        return False

    def extract(self, workbook: Workbook, *, source_name: str = "") -> BankStatement:
        # Find sheet containing the table
        target_sheet = None
        header_row_idx = None
        col_map: dict[str, int] = {}

        for sheet in workbook.sheets:
            for row in sheet.rows[:50]:
                for c_idx, cell in enumerate(row.cells):
                    txt = normalize_text(cell.value)
                    if "tran. id" in txt or "tran id" in txt:
                        # Found candidate header row
                        header_row_idx = row.index
                        target_sheet = sheet
                        break
                if header_row_idx is not None:
                    # Map columns dynamically from this row
                    for c_idx, cell in enumerate(row.cells):
                        txt = normalize_text(cell.value)
                        if "s.n." in txt:
                            col_map["sn"] = c_idx
                        elif "tran. id" in txt or "tran id" in txt:
                            col_map["tran_id"] = c_idx
                        elif "value date" in txt:
                            col_map["val_date"] = c_idx
                        elif "transaction date" in txt:
                            col_map["txn_date"] = c_idx
                        elif "posted date" in txt:
                            col_map["posted_date"] = c_idx
                        elif "cheque" in txt or "ref. no" in txt:
                            col_map["ref"] = c_idx
                        elif "remarks" in txt:
                            col_map["remarks"] = c_idx
                        elif "withdrawal" in txt:
                            col_map["withdrawal"] = c_idx
                        elif "deposit" in txt:
                            col_map["deposit"] = c_idx
                        elif "balance" in txt:
                            col_map["balance"] = c_idx
                    break
            if header_row_idx is not None:
                break

        if target_sheet is None or header_row_idx is None:
            raise ValueError("Could not find ICICI statement table header.")

        # Extract metadata from rows before the table
        metadata_map: dict[str, tuple[str, Provenance]] = {}
        for row in target_sheet.rows:
            if row.index >= header_row_idx:
                break
            for c_idx, cell in enumerate(row.cells):
                txt = str(cell.value or "").strip()
                if txt.endswith(":"):
                    label = txt[:-1].strip().lower()
                    if c_idx + 1 < len(row.cells):
                        val_cell = row.cells[c_idx + 1]
                        val_str = str(val_cell.value or "").strip()
                        if val_str:
                            metadata_map[label] = (
                                val_str,
                                Provenance.from_cell_location(val_cell.location, source=source_name),
                            )

        # Extract account info
        ac_num = metadata_map.get("a/c no", ("", None))[0]
        ac_type = metadata_map.get("a/c type", ("", None))[0]
        ifsc = metadata_map.get("ifsc code", ("", None))[0]
        branch_addr = metadata_map.get("branch address", ("", None))[0]
        holder_name = metadata_map.get("name", ("", None))[0]
        holder_addr = metadata_map.get("address", ("", None))[0]

        account: Account | None = None
        if ac_num:
            account = Account(
                id=f"acc:icici:{ac_num}",
                account_number=ac_num,
                account_type=ac_type or None,
                institution_name="ICICI Bank Ltd.",
                ifsc_code=ifsc or None,
                currency="INR",
            )

        holder: Party | None = None
        if holder_name:
            holder_slug = re.sub(r"[^a-zA-Z0-9]+", "_", holder_name.strip()).lower()
            holder = Party(
                id=f"party:{holder_slug}",
                name=holder_name,
                address=holder_addr or None,
            )

        institution = Party(
            id="party:icici_bank",
            name="ICICI Bank Ltd.",
            address=branch_addr or None,
        )

        # Period extraction
        period: DatePeriod | None = None
        for row in target_sheet.rows:
            if row.index >= header_row_idx:
                break
            for cell in row.cells:
                txt = str(cell.value or "")
                period_match = re.search(r"From\s+(\d{2}/\d{2}/\d{4})\s+To\s+(\d{2}/\d{2}/\d{4})", txt, re.IGNORECASE)
                if period_match:
                    period = DatePeriod(start_date=period_match.group(1), end_date=period_match.group(2))
                    break
            if period:
                break

        # Transactions
        transactions: list[Transaction] = []
        consecutive_empty = 0

        for row in target_sheet.rows:
            if row.index <= header_row_idx:
                continue

            first_val = str(row.cells[0].value or "").strip() if row.cells else ""
            norm_first = first_val.lower()

            # End of transaction table markers
            if norm_first.startswith("page total") or norm_first.startswith("opening bal") or norm_first.startswith("legends used"):
                break

            # Check if empty row
            has_content = any(c.value is not None and str(c.value).strip() != "" for c in row.cells)
            if not has_content:
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    break
                continue
            consecutive_empty = 0

            # Get values by mapped column index
            def get_val(key: str) -> str:
                idx = col_map.get(key)
                if idx is not None and idx < len(row.cells):
                    v = row.cells[idx].value
                    return str(v).strip() if v is not None else ""
                return ""

            sn = get_val("sn")
            tran_id = get_val("tran_id")
            val_date = get_val("val_date")
            txn_date = get_val("txn_date")
            ref = get_val("ref")
            remarks = get_val("remarks")
            withdrawal_str = get_val("withdrawal")
            deposit_str = get_val("deposit")
            balance_str = get_val("balance")

            # Must have either withdrawal or deposit, or tran_id
            withdrawal_dec = parse_decimal(withdrawal_str, default=Decimal("0")) or Decimal("0")
            deposit_dec = parse_decimal(deposit_str, default=Decimal("0")) or Decimal("0")
            balance_dec = parse_decimal(balance_str)

            if withdrawal_dec > Decimal("0"):
                amount = withdrawal_dec
                direction = TransactionDirection.DEBIT
            elif deposit_dec > Decimal("0"):
                amount = deposit_dec
                direction = TransactionDirection.CREDIT
            else:
                # Not a transaction row
                continue

            active_cells = [c.location for c in row.cells if c.value is not None]
            provenance = Provenance.from_cells(
                active_cells,
                source=source_name,
                sheet=target_sheet.name,
                row=row.index,
            )

            # Counterparty
            counterparty_party: Party | None = None
            cp_name = extract_counterparty_from_narration(remarks)
            if cp_name:
                cp_slug = re.sub(r"[^a-zA-Z0-9]+", "_", cp_name.strip()).lower()
                counterparty_party = Party(
                    id=f"party:{cp_slug}",
                    name=cp_name,
                )

            txn_id = f"txn:{tran_id or sn or row.index}"
            transactions.append(
                Transaction(
                    id=txn_id,
                    date=txn_date or val_date or "",
                    value_date=val_date or None,
                    amount=amount,
                    direction=direction,
                    currency="INR",
                    narration=remarks,
                    balance=balance_dec,
                    reference=ref or None,
                    counterparty=counterparty_party,
                    provenance=provenance,
                )
            )

        # Post-table summary balances
        opening_balance: Decimal | None = None
        closing_balance: Decimal | None = None

        for row in target_sheet.rows:
            if row.index < header_row_idx:
                continue
            for c_idx, cell in enumerate(row.cells):
                txt = normalize_text(cell.value)
                if "opening bal" in txt and c_idx + 1 < len(row.cells):
                    opening_balance = parse_decimal(row.cells[c_idx + 1].value)
                elif "closing bal" in txt and c_idx + 1 < len(row.cells):
                    closing_balance = parse_decimal(row.cells[c_idx + 1].value)

        # Fallback for closing balance if not printed in summary: use last transaction's balance
        if closing_balance is None and transactions and transactions[-1].balance is not None:
            closing_balance = transactions[-1].balance

        statement_id = f"stmt:icici:{ac_num or 'unknown'}:{period.start_date if period else 'statement'}"
        statement_provenance = Provenance(
            source=source_name,
            sheet=target_sheet.name,
            metadata={"extractor": self.name},
        )

        return BankStatement(
            id=statement_id,
            account=account,
            holder=holder,
            institution=institution,
            period=period,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            currency="INR",
            transactions=transactions,
            provenance=statement_provenance,
            metadata={"bank": "ICICI", "format": "excel_detailed"},
        )
