"""Standard / Generic tabular bank statement extractor."""

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


class StandardBankStatementExtractor:
    """Extractor for standard tabular bank statements (CSV or Excel) with columns:

    Date | Narration/Description | Debit/Withdrawal | Credit/Deposit | Balance
    """

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.BANK_STATEMENT

    @property
    def name(self) -> str:
        return "standard_bank_statement"

    @property
    def is_generic(self) -> bool:
        return True

    def matches(self, workbook: Workbook) -> bool:
        for sheet in workbook.sheets:
            # First check if document is explicitly a ledger
            for row in sheet.rows[:15]:
                texts = [normalize_text(c.value) for c in row.cells if c.value is not None]
                joined = " ".join(texts)
                if any(k in joined for k in ["general ledger", "ledger name", "ledger account", "tally"]):
                    return False

            for row in sheet.rows[:25]:
                texts = [normalize_text(c.value) for c in row.cells if c.value is not None]
                has_date = any("date" in t for t in texts)
                has_desc = any(
                    any(k in t for k in ["narration", "description", "particular", "details", "remark"])
                    for t in texts
                )
                has_debit = any(any(k in t for k in ["debit", "withdrawal", "dr", "outflow"]) for t in texts)
                has_credit = any(any(k in t for k in ["credit", "deposit", "cr", "inflow"]) for t in texts)

                if has_date and has_desc and (has_debit or has_credit):
                    return True
        return False

    def extract(self, workbook: Workbook, *, source_name: str = "") -> BankStatement:
        target_sheet = None
        header_row_idx = None
        col_map: dict[str, int] = {}

        for sheet in workbook.sheets:
            for row in sheet.rows[:30]:
                texts = [normalize_text(c.value) for c in row.cells]
                has_date = any("date" in t for t in texts)
                has_desc = any(any(k in t for k in ["narration", "description", "particular", "details"]) for t in texts)
                has_debit_credit = any(any(k in t for k in ["debit", "withdrawal", "credit", "deposit", "dr", "cr"]) for t in texts)

                if has_date and (has_desc or has_debit_credit):
                    header_row_idx = row.index
                    target_sheet = sheet
                    for c_idx, cell in enumerate(row.cells):
                        txt = normalize_text(cell.value)
                        if "date" in txt and "val" not in txt:
                            col_map["date"] = c_idx
                        elif "val" in txt and "date" in txt:
                            col_map["val_date"] = c_idx
                        elif any(k in txt for k in ["narration", "description", "particular", "details", "remarks"]):
                            col_map["narration"] = c_idx
                        elif any(k in txt for k in ["debit", "withdrawal", "dr", "outflow"]):
                            col_map["debit"] = c_idx
                        elif any(k in txt for k in ["credit", "deposit", "cr", "inflow"]):
                            col_map["credit"] = c_idx
                        elif "balance" in txt:
                            col_map["balance"] = c_idx
                        elif any(k in txt for k in ["chq", "ref", "cheque"]):
                            col_map["ref"] = c_idx
                    break
            if header_row_idx is not None:
                break

        if target_sheet is None or header_row_idx is None:
            raise ValueError("Standard bank statement header not found.")

        # Metadata scan before table
        account_number = None
        account_type = None
        ifsc_code = None
        branch_name = None
        holder_name = None
        institution_name = None
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

                if any(k in key_part for k in ["account no", "a/c no", "account number"]) and not account_number:
                    account_number = final_val
                elif any(k in key_part for k in ["account type", "a/c type"]) and not account_type:
                    account_type = final_val
                elif any(k in key_part for k in ["ifsc", "routing", "sort code", "swift", "bic"]) and not ifsc_code:
                    ifsc_code = final_val
                elif any(k in key_part for k in ["name", "account holder", "holder"]) and not holder_name:
                    holder_name = final_val
                elif any(k in key_part for k in ["bank", "institution", "branch address"]) and not institution_name:
                    institution_name = final_val.split(",")[0].strip() if "branch" in key_part else final_val
                elif any(k in key_part for k in ["branch", "a/c branch"]) and not branch_name:
                    branch_name = final_val
                elif "opening" in key_part and "bal" in key_part and opening_balance is None:
                    opening_balance = parse_decimal(final_val)

        transactions: list[Transaction] = []
        for row in target_sheet.rows:
            if row.index <= header_row_idx:
                continue

            # Check if row is empty
            if not any(c.value is not None and str(c.value).strip() != "" for c in row.cells):
                continue

            def get_cell_val(key: str) -> str:
                idx = col_map.get(key)
                if idx is not None and idx < len(row.cells):
                    v = row.cells[idx].value
                    return str(v).strip() if v is not None else ""
                return ""

            date_str = get_cell_val("date")
            val_date_str = get_cell_val("val_date")
            narration_str = get_cell_val("narration")
            debit_str = get_cell_val("debit")
            credit_str = get_cell_val("credit")
            balance_str = get_cell_val("balance")
            ref_str = get_cell_val("ref")

            # Check for footer / total rows
            first_val = normalize_text(row.cells[0].value)
            if any(k in first_val for k in ["total", "closing bal", "summary", "opening bal"]):
                for c_idx, cell in enumerate(row.cells):
                    txt = normalize_text(cell.value)
                    if "closing" in txt and "bal" in txt and c_idx + 1 < len(row.cells):
                        closing_balance = parse_decimal(row.cells[c_idx + 1].value)
                break

            debit_dec = parse_decimal(debit_str, default=Decimal("0")) or Decimal("0")
            credit_dec = parse_decimal(credit_str, default=Decimal("0")) or Decimal("0")
            balance_dec = parse_decimal(balance_str)

            if debit_dec > Decimal("0"):
                amount = debit_dec
                direction = TransactionDirection.DEBIT
            elif credit_dec > Decimal("0"):
                amount = credit_dec
                direction = TransactionDirection.CREDIT
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
            cp_name = extract_counterparty_from_narration(narration_str)
            if cp_name:
                cp_slug = re.sub(r"[^a-zA-Z0-9]+", "_", cp_name.strip()).lower()
                counterparty = Party(id=f"party:{cp_slug}", name=cp_name)

            txn_id = f"txn:{len(transactions) + 1}"
            transactions.append(
                Transaction(
                    id=txn_id,
                    date=date_str,
                    value_date=val_date_str or None,
                    amount=amount,
                    direction=direction,
                    narration=narration_str,
                    balance=balance_dec,
                    reference=ref_str or None,
                    counterparty=counterparty,
                    provenance=provenance,
                )
            )

        account: Account | None = None
        if account_number:
            account = Account(
                id=f"acc:{account_number}",
                account_number=account_number,
                account_type=account_type,
                ifsc_code=ifsc_code,
                institution_name=institution_name,
            )

        holder: Party | None = None
        if holder_name:
            holder_slug = re.sub(r"[^a-zA-Z0-9]+", "_", holder_name.strip()).lower()
            holder = Party(id=f"party:{holder_slug}", name=holder_name)

        institution: Party | None = None
        if institution_name:
            inst_slug = re.sub(r"[^a-zA-Z0-9]+", "_", institution_name.strip()).lower()
            institution = Party(id=f"party:{inst_slug}", name=institution_name)

        if closing_balance is None and transactions and transactions[-1].balance is not None:
            closing_balance = transactions[-1].balance

        # If opening balance was not explicitly printed, derive it from first transaction and balance if available
        if opening_balance is None and transactions:
            first_txn = transactions[0]
            if first_txn.balance is not None:
                if first_txn.direction == TransactionDirection.CREDIT:
                    opening_balance = first_txn.balance - first_txn.amount
                else:
                    opening_balance = first_txn.balance + first_txn.amount

        period: DatePeriod | None = None
        if transactions:
            period = DatePeriod(start_date=transactions[0].date, end_date=transactions[-1].date)

        return BankStatement(
            id=f"stmt:{account_number or 'standard'}:{period.start_date if period else 'statement'}",
            account=account,
            holder=holder,
            institution=institution,
            period=period,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            currency="INR",
            transactions=transactions,
            provenance=Provenance(source=source_name, sheet=target_sheet.name, metadata={"extractor": self.name}),
        )
