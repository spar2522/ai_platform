"""Deterministic extractor for Axis Bank statement layouts (both Tabular Excel and Multiline PDF)."""

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
from aip_canonica.models import Sheet, Workbook


class AxisBankStatementExtractor:
    """Extractor for Axis Bank statements supporting both flat tabular and wrapped multiline layouts."""

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.BANK_STATEMENT

    @property
    def name(self) -> str:
        return "axis_bank_statement"

    @property
    def is_generic(self) -> bool:
        return False

    def matches(self, workbook: Workbook) -> bool:
        """Anchor-based matching for Axis Bank signatures across any sheet."""
        for sheet in workbook.sheets:
            for row in sheet.rows[:40]:
                row_texts = [normalize_text(c.value) for c in row.cells if c.value is not None]
                joined = " ".join(row_texts)
                if "axis bank" in joined:
                    return True
                if "statement of axis account" in joined:
                    return True
                if "utib" in joined:
                    return True
                if "statement of account no" in joined and ("5145922811" in joined or "utib" in joined):
                    return True
        return False

    def extract(self, workbook: Workbook, *, source_name: str = "") -> BankStatement:
        """Extract canonical BankStatement from Axis Bank workbook."""
        # Find sheet containing the transactions
        target_sheet: Sheet | None = None
        is_tabular = False

        for sheet in workbook.sheets:
            for row in sheet.rows[:35]:
                row_texts = [normalize_text(c.value) for c in row.cells if c.value is not None]
                # Check for tabular header (e.g. SRL NO, Tran Date, Particulars, DR, CR, BAL)
                if any("tran date" in t for t in row_texts) and (
                    any("dr" == t or "dr" in t.split() for t in row_texts)
                    or any("cr" == t or "cr" in t.split() for t in row_texts)
                ):
                    target_sheet = sheet
                    is_tabular = True
                    break
                # Check for multiline PDF header (e.g. Tran Date, Particulars, Debit, Credit, Balance)
                if any("tran date" in t for t in row_texts) and any("balance" in t for t in row_texts):
                    target_sheet = sheet
                    is_tabular = False
                    break
            if target_sheet is not None:
                break

        if target_sheet is None:
            # Fallback to first sheet
            target_sheet = workbook.sheets[0]

        # Extract institution & holder metadata
        account_number, ifsc_code, customer_id, holder_name, address, period = self._extract_metadata(
            workbook, target_sheet
        )

        account: Account | None = None
        if account_number:
            account = Account(
                id=f"acc:axis:{account_number}",
                account_number=account_number,
                account_type="Savings",
                institution_name="Axis Bank Ltd.",
                ifsc_code=ifsc_code or "UTIB0005157",
                currency="INR",
            )

        holder: Party | None = None
        if holder_name:
            holder_slug = re.sub(r"[^a-zA-Z0-9]+", "_", holder_name.strip()).lower()
            holder = Party(
                id=f"party:{holder_slug}",
                name=holder_name,
                address=address or None,
            )

        institution = Party(
            id="party:axis_bank",
            name="Axis Bank Ltd.",
            address="TRISHUL, Opp. Samartheswar Temple, Near Law Garden, Ellisbridge, Ahmedabad - 380006",
        )

        # Delegate transaction extraction based on detected layout
        if is_tabular:
            transactions, opening_bal, closing_bal = self._extract_tabular(target_sheet, source_name)
        else:
            transactions, opening_bal, closing_bal = self._extract_multiline(target_sheet, source_name)

        statement_id = f"stmt:axis:{account_number or 'unknown'}:{period.start_date if period else 'statement'}"
        statement_provenance = Provenance(
            source=source_name,
            sheet=target_sheet.name,
            metadata={"extractor": self.name, "layout": "tabular" if is_tabular else "multiline"},
        )

        return BankStatement(
            id=statement_id,
            account=account,
            holder=holder,
            institution=institution,
            period=period,
            opening_balance=opening_bal,
            closing_balance=closing_bal,
            currency="INR",
            transactions=transactions,
            provenance=statement_provenance,
            metadata={"bank": "Axis Bank", "layout": "tabular" if is_tabular else "multiline"},
        )

    def _extract_metadata(
        self, workbook: Workbook, target_sheet: Sheet
    ) -> tuple[str, str, str, str, str, DatePeriod | None]:
        account_number = ""
        ifsc_code = ""
        customer_id = ""
        holder_name = ""
        address_parts: list[str] = []
        period: DatePeriod | None = None

        for sheet in workbook.sheets:
            for row in sheet.rows[:35]:
                for cell in row.cells:
                    txt = str(cell.value or "").strip()
                    if not txt:
                        continue

                    # Account Number
                    ac_m = re.search(r"Statement of (?:Axis )?Account No\s*[:-]?\s*([0-9]+)", txt, re.IGNORECASE)
                    if ac_m and not account_number:
                        account_number = ac_m.group(1)

                    # Period
                    p_m = re.search(
                        r"From\s*:\s*(\d{2}[-/]\d{2}[-/]\d{4})\s*To\s*:\s*(\d{2}[-/]\d{2}[-/]\d{4})",
                        txt,
                        re.IGNORECASE,
                    )
                    if p_m and period is None:
                        period = DatePeriod(start_date=p_m.group(1), end_date=p_m.group(2))

                    # Customer ID
                    c_m = re.search(r"Customer ID\s*[:-]?\s*([0-9]+)", txt, re.IGNORECASE)
                    if c_m and not customer_id:
                        customer_id = c_m.group(1)

                    # IFSC Code
                    if_m = re.search(r"IFSC Code\s*[:-]?\s*([A-Za-z0-9]+)", txt, re.IGNORECASE)
                    if if_m and not ifsc_code:
                        ifsc_code = if_m.group(1)

                    # Name
                    n_m = re.search(r"^Name\s*[:-]+\s*(.+)", txt, re.IGNORECASE)
                    if n_m and not holder_name:
                        holder_name = n_m.group(1).strip()

        # Holder Name fallback from first few rows of target sheet if not prefixed with "Name :-"
        if not holder_name and target_sheet.rows:
            r0 = target_sheet.rows[0]
            val0 = str(r0.cells[0].value or "").strip() if r0.cells else ""
            if val0 and not any(k in val0.lower() for k in ["statement", "axis", "customer", "joint"]):
                holder_name = val0

        # Collect address parts
        for row in target_sheet.rows[2:8]:
            row_txt = " ".join(str(c.value).strip() for c in row.cells if c.value is not None)
            if any(k in row_txt.lower() for k in ["customer id", "ifsc code", "statement of", "nominee"]):
                # Stop address parsing before customer info
                break
            if row_txt and "joint holder" not in row_txt.lower():
                address_parts.append(row_txt)

        address = ", ".join(address_parts).strip()
        return account_number, ifsc_code, customer_id, holder_name, address, period

    def _extract_tabular(
        self, sheet: Sheet, source_name: str
    ) -> tuple[list[Transaction], Decimal | None, Decimal | None]:
        """Extract transactions from flat 2D spreadsheet layout."""
        header_row_idx: int | None = None
        col_map: dict[str, int] = {}

        for row in sheet.rows[:30]:
            row_texts = [str(c.value).strip().lower() for c in row.cells if c.value is not None]
            if "tran date" in row_texts and ("dr" in row_texts or "cr" in row_texts):
                header_row_idx = row.index
                for c_idx, cell in enumerate(row.cells):
                    val = str(cell.value or "").strip().lower()
                    if "srl no" in val:
                        col_map["srl_no"] = c_idx
                    elif "tran date" in val:
                        col_map["date"] = c_idx
                    elif "chqno" in val or "chq" in val:
                        col_map["chq"] = c_idx
                    elif "particulars" in val:
                        col_map["narration"] = c_idx
                    elif val == "dr":
                        col_map["dr"] = c_idx
                    elif val == "cr":
                        col_map["cr"] = c_idx
                    elif "bal" in val:
                        col_map["bal"] = c_idx
                break

        if header_row_idx is None:
            raise ValueError("Could not find Axis Bank tabular statement header.")

        transactions: list[Transaction] = []
        opening_balance: Decimal | None = None
        closing_balance: Decimal | None = None

        for row in sheet.rows:
            if row.index <= header_row_idx:
                continue

            joined = " ".join(str(c.value).strip() for c in row.cells if c.value is not None)
            if not joined or "unless the constituent" in joined.lower() or "legend" in joined.lower():
                break

            def get_col(key: str) -> str:
                idx = col_map.get(key)
                if idx is not None and idx < len(row.cells):
                    v = row.cells[idx].value
                    return str(v).strip() if v is not None else ""
                return ""

            txn_date = get_col("date")
            if not txn_date or not re.match(r"^\d{2}-\d{2}-\d{4}", txn_date):
                continue

            narration = get_col("narration")
            chq = get_col("chq")
            dr_dec = parse_decimal(get_col("dr"), default=Decimal("0")) or Decimal("0")
            cr_dec = parse_decimal(get_col("cr"), default=Decimal("0")) or Decimal("0")
            bal_dec = parse_decimal(get_col("bal"))

            if dr_dec > Decimal("0"):
                amount = dr_dec
                direction = TransactionDirection.DEBIT
            elif cr_dec > Decimal("0"):
                amount = cr_dec
                direction = TransactionDirection.CREDIT
            else:
                continue

            # Compute initial opening balance from first transaction
            if opening_balance is None and bal_dec is not None:
                if direction == TransactionDirection.CREDIT:
                    opening_balance = bal_dec - amount
                else:
                    opening_balance = bal_dec + amount

            closing_balance = bal_dec

            active_cells = [c.location for c in row.cells if c.value is not None]
            provenance = Provenance.from_cells(
                active_cells,
                source=source_name,
                sheet=sheet.name,
                row=row.index,
            )

            # Counterparty
            counterparty_party: Party | None = None
            cp_name = extract_counterparty_from_narration(narration)
            if cp_name:
                cp_slug = re.sub(r"[^a-zA-Z0-9]+", "_", cp_name.strip()).lower()
                counterparty_party = Party(id=f"party:{cp_slug}", name=cp_name)

            srl = get_col("srl_no")
            txn_id = f"txn:axis:{srl or row.index}"
            transactions.append(
                Transaction(
                    id=txn_id,
                    date=txn_date,
                    amount=amount,
                    direction=direction,
                    currency="INR",
                    narration=narration,
                    balance=bal_dec,
                    reference=chq if chq and chq != "-" else None,
                    counterparty=counterparty_party,
                    provenance=provenance,
                )
            )

        return transactions, opening_balance, closing_balance

    def _extract_multiline(
        self, sheet: Sheet, source_name: str
    ) -> tuple[list[Transaction], Decimal | None, Decimal | None]:
        """Extract transactions from multi-line wrapped visual layout (PDF)."""
        opening_balance: Decimal | None = None
        closing_balance: Decimal | None = None

        # 1. Locate opening balance
        for row in sheet.rows:
            joined = " ".join(str(c.value).strip() for c in row.cells if c.value is not None)
            if "OPENING BALANCE" in joined:
                m = re.search(r"OPENING BALANCE\s*(\d+\.\d{2})", joined)
                if m:
                    opening_balance = Decimal(m.group(1))
                else:
                    for c in row.cells:
                        val = parse_decimal(c.value)
                        if val is not None:
                            opening_balance = val
                            break
                break

        transactions: list[Transaction] = []
        current_balance = opening_balance
        i = 0

        while i < len(sheet.rows):
            row = sheet.rows[i]
            joined = " ".join(str(c.value).strip() for c in row.cells if c.value is not None)

            if "TRANSACTION TOTAL" in joined or "CLOSING BALANCE" in joined:
                if "CLOSING BALANCE" in joined:
                    m = re.search(r"CLOSING BALANCE\s*(\d+\.\d{2})", joined)
                    if m:
                        closing_balance = Decimal(m.group(1))
                    else:
                        for c in row.cells:
                            parsed_val = parse_decimal(c.value)
                            if parsed_val is not None:
                                closing_balance = parsed_val
                                break
                break

            date_match = re.match(r"^(\d{2}-\d{2}-\d{4})", joined)
            if date_match:
                txn_date = date_match.group(1)
                narration_parts: list[str] = []
                active_cells = [c.location for c in row.cells if c.value is not None]

                bal_val: Decimal | None = None
                amt_val: Decimal | None = None

                # Inspect cells in the starting row
                for cell in row.cells:
                    cell_str = str(cell.value or "").strip()
                    if not cell_str:
                        continue
                    m_bal = re.match(r"^(\d+\.\d{2})\s+\d+$", cell_str)
                    if m_bal:
                        bal_val = Decimal(m_bal.group(1))
                        continue
                    m_amt = re.match(r"^(\d+\.\d{2})$", cell_str)
                    if m_amt:
                        amt_val = Decimal(m_amt.group(1))
                        continue
                    # Narration text
                    cleaned = cell_str
                    if cleaned.startswith(txn_date):
                        cleaned = cleaned[len(txn_date):].strip()
                    if cleaned:
                        narration_parts.append(cleaned)

                # If balance is not in this starting row, scan subsequent rows
                if bal_val is None:
                    while i + 1 < len(sheet.rows):
                        i += 1
                        sub_row = sheet.rows[i]
                        sub_joined = " ".join(str(c.value).strip() for c in sub_row.cells if c.value is not None)
                        if "TRANSACTION TOTAL" in sub_joined or "CLOSING BALANCE" in sub_joined:
                            break
                        for c in sub_row.cells:
                            if c.value is not None:
                                active_cells.append(c.location)
                            sub_cell_str = str(c.value or "").strip()
                            if not sub_cell_str:
                                continue
                            m_bal = re.match(r"^(\d+\.\d{2})\s+\d+$", sub_cell_str)
                            if m_bal:
                                bal_val = Decimal(m_bal.group(1))
                                continue
                            m_amt = re.match(r"^(\d+\.\d{2})$", sub_cell_str)
                            if m_amt:
                                amt_val = Decimal(m_amt.group(1))
                                continue
                            narration_parts.append(sub_cell_str)

                        if bal_val is not None:
                            break

                # Resolve transaction details if balance was discovered
                if bal_val is not None:
                    if current_balance is not None:
                        if bal_val > current_balance:
                            direction = TransactionDirection.CREDIT
                            computed_amt = bal_val - current_balance
                        else:
                            direction = TransactionDirection.DEBIT
                            computed_amt = current_balance - bal_val
                        amount = amt_val if amt_val is not None else computed_amt
                    else:
                        # Fallback if no opening balance known yet
                        amount = amt_val or Decimal("0")
                        direction = TransactionDirection.CREDIT

                    current_balance = bal_val
                    narration = " ".join(narration_parts).strip()

                    # Counterparty extraction
                    counterparty_party: Party | None = None
                    cp_name = extract_counterparty_from_narration(narration)
                    if cp_name:
                        cp_slug = re.sub(r"[^a-zA-Z0-9]+", "_", cp_name.strip()).lower()
                        counterparty_party = Party(id=f"party:{cp_slug}", name=cp_name)

                    provenance = Provenance.from_cells(
                        active_cells,
                        source=source_name,
                        sheet=sheet.name,
                        row=row.index,
                    )

                    txn_id = f"txn:axis:{len(transactions) + 1}"
                    transactions.append(
                        Transaction(
                            id=txn_id,
                            date=txn_date,
                            amount=amount,
                            direction=direction,
                            currency="INR",
                            narration=narration,
                            balance=bal_val,
                            counterparty=counterparty_party,
                            provenance=provenance,
                        )
                    )

            i += 1

        if closing_balance is None:
            closing_balance = current_balance

        return transactions, opening_balance, closing_balance
