"""Tabular ledger extractor converting ledger documents (CSV or Excel) into canonical Ledger models."""

from __future__ import annotations

from decimal import Decimal
import re

from aip_canonica.extractors.helpers import extract_counterparty_from_narration, normalize_text, parse_decimal
from aip_canonica.models import Workbook
from aip_canonica.models.base import DatePeriod
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models.ledger import EntryDirection, Ledger, LedgerEntry
from aip_canonica.models.party import Account, Party
from aip_canonica.models.provenance import Provenance


class TabularLedgerExtractor:
    """Deterministic extractor for general ledger and sub-ledger documents."""

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.LEDGER

    @property
    def name(self) -> str:
        return "tabular_ledger"

    @property
    def is_generic(self) -> bool:
        return True

    def matches(self, workbook: Workbook) -> bool:
        for sheet in workbook.sheets:
            has_ledger_keyword = False
            has_cols = False
            for row in sheet.rows[:30]:
                texts = [normalize_text(c.value) for c in row.cells if c.value is not None]
                joined = " ".join(texts)
                if any(k in joined for k in ["ledger", "general ledger", "account statement", "tally"]):
                    has_ledger_keyword = True

                has_date = any("date" in t for t in texts)
                has_part = any(any(k in t for k in ["particular", "narration", "description"]) for t in texts)
                has_debit = any(any(k in t for k in ["debit", "dr"]) for t in texts)
                has_credit = any(any(k in t for k in ["credit", "cr"]) for t in texts)

                if has_date and has_part and (has_debit or has_credit):
                    has_cols = True

            # If it has strong ledger keywords and columns, or standard ledger columns with "ledger" or "particulars"
            if (has_ledger_keyword and has_cols) or (has_cols and any("particular" in normalize_text(c.value) for r in sheet.rows[:15] for c in r.cells)):
                return True
        return False

    def extract(self, workbook: Workbook, *, source_name: str = "") -> Ledger:
        target_sheet = None
        header_row_idx = None
        col_map: dict[str, int] = {}

        for sheet in workbook.sheets:
            for row in sheet.rows[:30]:
                texts = [normalize_text(c.value) for c in row.cells]
                has_date = any("date" in t for t in texts)
                has_part = any(any(k in t for k in ["particular", "narration", "description"]) for t in texts)
                has_debit = any(any(k in t for k in ["debit", "dr"]) for t in texts)
                has_credit = any(any(k in t for k in ["credit", "cr"]) for t in texts)

                if has_date and (has_part or (has_debit and has_credit)):
                    header_row_idx = row.index
                    target_sheet = sheet
                    for c_idx, cell in enumerate(row.cells):
                        txt = normalize_text(cell.value)
                        if "date" in txt:
                            col_map["date"] = c_idx
                        elif any(k in txt for k in ["particular", "narration", "description"]):
                            col_map["particulars"] = c_idx
                        elif any(k in txt for k in ["debit", "dr"]):
                            col_map["debit"] = c_idx
                        elif any(k in txt for k in ["credit", "cr"]):
                            col_map["credit"] = c_idx
                        elif "balance" in txt:
                            col_map["balance"] = c_idx
                        elif any(k in txt for k in ["ref", "vch", "voucher"]):
                            col_map["ref"] = c_idx
                    break
            if header_row_idx is not None:
                break

        if target_sheet is None or header_row_idx is None:
            raise ValueError("Could not find ledger table header.")

        # Metadata scan above table
        ledger_name = target_sheet.name
        account_name = None
        party_name = None
        opening_balance = None
        closing_balance = None

        for row in target_sheet.rows:
            if row.index >= header_row_idx:
                break
            for c_idx, cell in enumerate(row.cells):
                raw_cell = str(cell.value or "").strip()
                if not raw_cell:
                    continue
                next_val = str(row.cells[c_idx + 1].value or "").strip() if c_idx + 1 < len(row.cells) else ""
                if ":" in raw_cell:
                    parts = raw_cell.split(":", 1)
                    key_part = normalize_text(parts[0])
                    val_part = parts[1].strip()
                else:
                    key_part = normalize_text(raw_cell)
                    val_part = ""

                final_val = val_part or next_val
                if not final_val:
                    continue

                if any(k in key_part for k in ["ledger name", "account", "ledger"]) and not account_name:
                    ledger_name = final_val
                    account_name = final_val
                elif any(k in key_part for k in ["party", "party name"]) and not party_name:
                    party_name = final_val
                elif "opening" in key_part and "bal" in key_part and opening_balance is None:
                    opening_balance = parse_decimal(final_val)

        entries: list[LedgerEntry] = []
        for row in target_sheet.rows:
            if row.index <= header_row_idx:
                continue

            first_val = normalize_text(row.cells[0].value if row.cells else "")
            if any(k in first_val for k in ["total", "closing bal", "summary"]):
                for c_idx, cell in enumerate(row.cells):
                    txt = normalize_text(cell.value)
                    if "closing" in txt and "bal" in txt and c_idx + 1 < len(row.cells):
                        closing_balance = parse_decimal(row.cells[c_idx + 1].value)
                break

            # Check if row is empty
            if not any(c.value is not None and str(c.value).strip() != "" for c in row.cells):
                continue

            def get_val(key: str) -> str:
                idx = col_map.get(key)
                if idx is not None and idx < len(row.cells):
                    v = row.cells[idx].value
                    return str(v).strip() if v is not None else ""
                return ""

            date_str = get_val("date")
            particulars_str = get_val("particulars")
            debit_str = get_val("debit")
            credit_str = get_val("credit")
            balance_str = get_val("balance")
            ref_str = get_val("ref")

            debit_dec = parse_decimal(debit_str, default=Decimal("0")) or Decimal("0")
            credit_dec = parse_decimal(credit_str, default=Decimal("0")) or Decimal("0")
            balance_dec = parse_decimal(balance_str)

            # Check if this row is an "Opening Balance" row inside the table
            if "opening balance" in normalize_text(particulars_str):
                opening_balance = balance_dec or (debit_dec if debit_dec > 0 else -credit_dec)
                continue

            if debit_dec > Decimal("0"):
                amount = debit_dec
                direction = EntryDirection.DEBIT
            elif credit_dec > Decimal("0"):
                amount = credit_dec
                direction = EntryDirection.CREDIT
            else:
                continue

            active_cells = [c.location for c in row.cells if c.value is not None]
            provenance = Provenance.from_cells(
                active_cells,
                source=source_name,
                sheet=target_sheet.name,
                row=row.index,
            )

            counterparty: Party | None = None
            cp_name = extract_counterparty_from_narration(particulars_str) or particulars_str
            if cp_name:
                cp_slug = re.sub(r"[^a-zA-Z0-9]+", "_", cp_name.strip()).lower()
                counterparty = Party(id=f"party:{cp_slug}", name=cp_name)

            entries.append(
                LedgerEntry(
                    id=f"entry:{len(entries) + 1}",
                    date=date_str,
                    narration=particulars_str,
                    amount=amount,
                    direction=direction,
                    balance=balance_dec,
                    reference=ref_str or None,
                    counterparty=counterparty,
                    provenance=provenance,
                )
            )

        if closing_balance is None and entries and entries[-1].balance is not None:
            closing_balance = entries[-1].balance

        account: Account | None = None
        if account_name:
            acc_slug = re.sub(r"[^a-zA-Z0-9]+", "_", account_name.strip()).lower()
            account = Account(id=f"acc:{acc_slug}", account_number=account_name)

        party: Party | None = None
        if party_name:
            party_slug = re.sub(r"[^a-zA-Z0-9]+", "_", party_name.strip()).lower()
            party = Party(id=f"party:{party_slug}", name=party_name)

        period: DatePeriod | None = None
        if entries:
            period = DatePeriod(start_date=entries[0].date, end_date=entries[-1].date)

        return Ledger(
            id=f"ledger:{re.sub(r'[^a-zA-Z0-9]+', '_', ledger_name).lower()}",
            name=ledger_name,
            account=account,
            party=party,
            period=period,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            currency="INR",
            entries=entries,
            provenance=Provenance(source=source_name, sheet=target_sheet.name, metadata={"extractor": self.name}),
        )
