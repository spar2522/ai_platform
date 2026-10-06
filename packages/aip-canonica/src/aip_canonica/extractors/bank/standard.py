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


def _is_date_header(t: str) -> bool:
    if ":" in t or len(t) > 30:
        return False
    return any(k in t for k in ["txn date", "trans date", "transaction date", "value date", "posting date"]) or bool(re.search(r"\bdate\b", t))


def _is_desc_header(t: str) -> bool:
    if ":" in t or len(t) > 35:
        return False
    return any(k in t for k in ["narration", "description", "particular", "particulars", "details", "remarks"])


def _is_debit_header(t: str) -> bool:
    if ":" in t or len(t) > 30:
        return False
    return any(k in t for k in ["debit", "withdrawal", "outflow"]) or bool(re.search(r"\bdr\.?\b", t))


def _is_credit_header(t: str) -> bool:
    if ":" in t or len(t) > 30:
        return False
    return any(k in t for k in ["credit", "deposit", "inflow"]) or bool(re.search(r"\bcr\.?\b", t))


def _is_amount_header(t: str) -> bool:
    if ":" in t or len(t) > 30:
        return False
    return bool(re.search(r"\bamount\b", t))


def _find_summary_value(rows: list, r_idx: int, c_idx: int) -> Decimal | None:
    row = rows[r_idx]
    cell = row.cells[c_idx]
    raw = str(cell.value or "").strip()

    # 1. Embedded key-value in single cell (e.g. "Opening Balance: 55,915.73")
    if ":" in raw:
        parts = raw.split(":", 1)
        val = parse_decimal(parts[1])
        if val is not None:
            return val

    # 2. Check next non-empty cell in the same row
    for next_c in row.cells[c_idx + 1: c_idx + 4]:
        if next_c.value is not None and str(next_c.value).strip():
            val = parse_decimal(next_c.value)
            if val is not None:
                return val
            break

    # 3. Check next row at c_idx (2-row horizontal summary table)
    if r_idx + 1 < len(rows):
        next_row = rows[r_idx + 1]
        if c_idx < len(next_row.cells):
            val = parse_decimal(next_row.cells[c_idx].value)
            if val is not None:
                return val
        if c_idx + 1 < len(next_row.cells):
            val = parse_decimal(next_row.cells[c_idx + 1].value)
            if val is not None:
                return val
    return None


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

            for row in sheet.rows[:35]:
                texts = [normalize_text(c.value) for c in row.cells if c.value is not None]
                has_date = any(_is_date_header(t) for t in texts)
                has_desc = any(_is_desc_header(t) for t in texts)
                has_debit = any(_is_debit_header(t) for t in texts)
                has_credit = any(_is_credit_header(t) for t in texts)
                has_amt = any(_is_amount_header(t) for t in texts)

                if has_date and has_desc and (has_debit or has_credit or has_amt):
                    return True
        return False

    def extract(self, workbook: Workbook, *, source_name: str = "") -> BankStatement:
        target_sheet = None
        header_row_idx = None
        col_map: dict[str, int] = {}

        for sheet in workbook.sheets:
            for row in sheet.rows[:35]:
                texts = [normalize_text(c.value) for c in row.cells]
                has_date = any(_is_date_header(t) for t in texts)
                has_desc = any(_is_desc_header(t) for t in texts)
                has_debit = any(_is_debit_header(t) for t in texts)
                has_credit = any(_is_credit_header(t) for t in texts)
                has_amt = any(_is_amount_header(t) for t in texts)

                if has_date and has_desc and (has_debit or has_credit or has_amt):
                    header_row_idx = row.index
                    target_sheet = sheet
                    for c_idx, cell in enumerate(row.cells):
                        txt = normalize_text(cell.value)
                        if _is_date_header(txt) and "val" not in txt:
                            col_map["date"] = c_idx
                        elif "val" in txt and _is_date_header(txt):
                            col_map["val_date"] = c_idx
                        elif _is_desc_header(txt):
                            col_map["narration"] = c_idx
                        elif _is_debit_header(txt):
                            col_map["debit"] = c_idx
                        elif _is_credit_header(txt):
                            col_map["credit"] = c_idx
                        elif any(k in txt for k in ["balance", "bal", "closing"]):
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
        extracted_period = None

        for row in target_sheet.rows:
            if row.index >= header_row_idx:
                break
            for c_idx, cell in enumerate(row.cells):
                raw_cell = str(cell.value or "").strip()
                if not raw_cell:
                    continue

                # Direct regex matching on full cell string for account number
                if not account_number:
                    acc_m = re.search(
                        r"(?:account\s*no|a/c\s*no|account\s*number)[^\w\d]*([A-Za-z0-9]+)",
                        raw_cell,
                        re.IGNORECASE,
                    )
                    if acc_m:
                        account_number = acc_m.group(1)

                # Period dates in cell
                if not extracted_period:
                    per_m = re.search(
                        r"(?:statement\s*)?from\s*[:\-]?\s*([0-9]{2}[\/\-][0-9]{2}[\/\-][0-9]{4}).*?to\s*[:\-]?\s*([0-9]{2}[\/\-][0-9]{2}[\/\-][0-9]{4})",
                        raw_cell,
                        re.IGNORECASE,
                    )
                    if per_m:
                        extracted_period = DatePeriod(start_date=per_m.group(1), end_date=per_m.group(2))

                # IFSC code
                if not ifsc_code:
                    ifsc_m = re.search(r"ifsc(?:\s*code)?\s*[:\-]+\s*([A-Za-z0-9]+)", raw_cell, re.IGNORECASE)
                    if ifsc_m:
                        ifsc_code = ifsc_m.group(1)

                # Holder name
                if not holder_name:
                    name_m = re.search(r"^(?:name|account\s*holder|primary\s*holder)\s*[:\-]+\s*([^\n,]+)", raw_cell, re.IGNORECASE)
                    if name_m:
                        holder_name = re.sub(r"^[:\-\s]+", "", name_m.group(1)).strip()

                # Bank / Institution name in top rows
                if not institution_name and row.index < 5:
                    bank_m = re.search(r"^([A-Za-z\s]+Bank(?:\s+Ltd\.?)?)", raw_cell, re.IGNORECASE)
                    if bank_m:
                        institution_name = bank_m.group(1).strip()

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

                if any(k in key_part for k in ["account type", "a/c type"]) and not account_type:
                    account_type = final_val
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

            # Check for footer / summary indicator row
            first_val = normalize_text(row.cells[0].value)
            joined_row = " ".join(normalize_text(c.value) for c in row.cells)
            if any(k in first_val for k in ["total", "closing bal", "summary", "opening bal"]) or \
               any(k in joined_row for k in ["statement summary", "grand total"]):
                break

            # A valid transaction row must have a non-empty transaction date
            if not date_str or normalize_text(date_str) in ["date", "txn date", "transaction date"]:
                continue

            # Check if row is an inline "Opening Balance" row within the transaction table
            if "opening" in normalize_text(narration_str) and "bal" in normalize_text(narration_str):
                for c in reversed(row.cells):
                    v = parse_decimal(c.value)
                    if v is not None:
                        opening_balance = v
                        break
                continue

            debit_dec = parse_decimal(debit_str, default=Decimal("0")) or Decimal("0")
            credit_dec = parse_decimal(credit_str, default=Decimal("0")) or Decimal("0")
            balance_dec = parse_decimal(balance_str)

            # Support ragged PDF/CSV rows where either debit or credit cell was omitted
            if balance_dec is None and "balance" in col_map and col_map["balance"] >= len(row.cells) and len(row.cells) >= 3:
                last_val = parse_decimal(row.cells[-1].value)
                if last_val is not None:
                    balance_dec = last_val
                    amt_val = parse_decimal(row.cells[-2].value)
                    if amt_val is not None and amt_val > Decimal("0"):
                        prev_bal = transactions[-1].balance if transactions else opening_balance
                        if prev_bal is not None:
                            if balance_dec > prev_bal:
                                credit_dec = amt_val
                                debit_dec = Decimal("0")
                            else:
                                debit_dec = amt_val
                                credit_dec = Decimal("0")
                        else:
                            nar_lower = normalize_text(narration_str)
                            if any(k in nar_lower for k in ["credit", "deposit", "inflow", "cr"]):
                                credit_dec = amt_val
                                debit_dec = Decimal("0")
                            else:
                                debit_dec = amt_val
                                credit_dec = Decimal("0")

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

        # Scan footer rows for Opening / Closing balances
        for r_idx, row in enumerate(target_sheet.rows):
            if r_idx <= header_row_idx:
                continue
            for c_idx, cell in enumerate(row.cells):
                txt = normalize_text(cell.value)
                if not txt:
                    continue
                if opening_balance is None and "opening" in txt and ("bal" in txt or "balance" in txt) and "date" not in txt:
                    val = _find_summary_value(target_sheet.rows, r_idx, c_idx)
                    if val is not None:
                        opening_balance = val
                elif closing_balance is None and "closing" in txt and ("bal" in txt or "balance" in txt):
                    val = _find_summary_value(target_sheet.rows, r_idx, c_idx)
                    if val is not None:
                        closing_balance = val

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

        # Check if transactions are in reverse-chronological (descending) order
        is_descending = False
        if len(transactions) >= 2 and transactions[0].balance is not None and transactions[1].balance is not None:
            delta = transactions[0].amount if transactions[0].direction == TransactionDirection.CREDIT else -transactions[0].amount
            if transactions[1].balance + delta == transactions[0].balance:
                is_descending = True

        if closing_balance is None and transactions:
            latest_txn = transactions[0] if is_descending else transactions[-1]
            if latest_txn.balance is not None:
                closing_balance = latest_txn.balance

        # If opening balance was not explicitly printed, derive it from earliest transaction and balance if available
        if opening_balance is None and transactions:
            earliest_txn = transactions[-1] if is_descending else transactions[0]
            if earliest_txn.balance is not None:
                if earliest_txn.direction == TransactionDirection.CREDIT:
                    opening_balance = earliest_txn.balance - earliest_txn.amount
                else:
                    opening_balance = earliest_txn.balance + earliest_txn.amount

        period: DatePeriod | None = extracted_period
        if period is None and transactions:
            if is_descending:
                period = DatePeriod(start_date=transactions[-1].date, end_date=transactions[0].date)
            else:
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
