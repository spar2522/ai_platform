"""Auto-synthesized deterministic tabular extractor for 'axis_bank_statement'."""

from __future__ import annotations

from decimal import Decimal
import re
from typing import Any

from aip_canonica.extractors.helpers import (
    extract_counterparty_from_narration,
    parse_decimal,
)
from aip_canonica.models import DocumentType, Workbook
from aip_canonica.models.bank_statement import BankStatement, Transaction
from aip_canonica.models.base import TransactionDirection
from aip_canonica.models.party import Account, Party
from aip_canonica.models.provenance import Provenance


class AxisBankStatementExtractor:
    """Auto-synthesized deterministic tabular extractor for 'axis_bank_statement' layouts."""

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
        anchors = [
            "utib0005157",
            "statement of account no",
            "statement of axis account no",
        ]
        headers_1 = ["srl no", "tran date", "chqno", "particulars", "dr", "cr", "bal"]
        headers_2 = ["tran date", "chq no", "particulars", "debit", "credit", "balance"]

        for sheet in workbook.sheets:
            for row in sheet.rows[:35]:
                row_text = " ".join(
                    str(c.value or "").lower() for c in row.cells if c.value is not None
                )
                if any(a in row_text for a in anchors):
                    return True
                if all(h in row_text for h in headers_1[:3]):
                    return True
                if all(h in row_text for h in headers_2[:3]):
                    return True
        return False

    def extract(self, workbook: Workbook, *, source_name: str = "") -> BankStatement:
        # Detect layout type (tabular vs multiline_block)
        is_multiline = False
        for sheet in workbook.sheets:
            for row in sheet.rows[:50]:
                row_str = " ".join(
                    str(c.value or "").strip() for c in row.cells if c.value is not None
                )
                if "statement of axis account no" in row_str.lower() or (
                    "|" in row_str and re.search(r"\d{2}-\d{2}-\d{4}", row_str)
                ):
                    is_multiline = True
                    break
            if is_multiline:
                break

        if is_multiline:
            return self._extract_multiline(workbook, source_name=source_name)
        else:
            return self._extract_tabular(workbook, source_name=source_name)

    def _extract_tabular(self, workbook: Workbook, source_name: str) -> BankStatement:
        sheet = workbook.sheets[0]
        col_mapping_spec = {
            "serial_number": "SRL NO",
            "date": "Tran Date",
            "reference": "CHQNO",
            "narration": "PARTICULARS",
            "debit": "DR",
            "credit": "CR",
            "balance": "BAL",
        }

        # 1. Locate header row and map column indices
        header_row_idx: int | None = None
        col_map: dict[str, int] = {}

        for row in sheet.rows[:40]:
            row_texts = [
                str(c.value or "").strip().lower()
                for c in row.cells
                if c.value is not None
            ]
            matches_count = 0
            for canonical_key, doc_header in col_mapping_spec.items():
                if any(doc_header.lower() in t for t in row_texts):
                    matches_count += 1
            if matches_count >= 2:
                header_row_idx = row.index
                for c_idx, cell in enumerate(row.cells):
                    txt = str(cell.value or "").strip().lower()
                    for canonical_key, doc_header in col_mapping_spec.items():
                        if doc_header.lower() in txt or txt in doc_header.lower():
                            col_map[canonical_key] = c_idx
                break

        if header_row_idx is None:
            raise ValueError(
                "Could not locate table header in 'axis_bank_statement' layout."
            )

        # 2. Extract institution and account metadata
        account_number = ""
        holder_name = ""
        for row in sheet.rows[:header_row_idx]:
            for cell in row.cells:
                val = str(cell.value or "").strip()
                if "account" in val.lower() and not account_number:
                    m = re.search(
                        r"(?:a/c|account|no)[^0-9]*([0-9A-Za-z]+)", val, re.IGNORECASE
                    )
                    if m:
                        account_number = m.group(1)
                if "name" in val.lower() and not holder_name:
                    m = re.search(r"name\s*[:-]+\s*(.+)", val, re.IGNORECASE)
                    if m:
                        holder_name = m.group(1)

        # 3. Extract transaction rows
        transactions: list[Transaction] = []
        opening_balance: Decimal | None = None
        closing_balance: Decimal | None = None

        for row in sheet.rows:
            if row.index <= header_row_idx:
                continue

            row_str = " ".join(
                str(c.value or "").strip() for c in row.cells if c.value is not None
            )
            if not row_str or any(
                stop in row_str.lower()
                for stop in ["page total", "closing balance", "legend", "unless"]
            ):
                break

            def get_val(key: str) -> str:
                idx = col_map.get(key)
                if idx is not None and idx < len(row.cells):
                    v = row.cells[idx].value
                    return str(v).strip() if v is not None else ""
                return ""

            txn_date = (
                get_val("date")
                or get_val("txn_date")
                or get_val("tran date")
                or get_val("tran_date")
            )
            if not txn_date or not re.search(r"\d", txn_date):
                continue

            narration = (
                get_val("description") or get_val("narration") or get_val("particulars")
            )
            debit_str = get_val("debit") or get_val("withdrawal") or get_val("dr")
            credit_str = get_val("credit") or get_val("deposit") or get_val("cr")
            balance_str = get_val("balance") or get_val("bal")

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

            if opening_balance is None and balance_dec is not None:
                if direction == TransactionDirection.CREDIT:
                    opening_balance = balance_dec - amount
                else:
                    opening_balance = balance_dec + amount

            closing_balance = balance_dec

            active_cells = [c.location for c in row.cells if c.value is not None]
            provenance = Provenance.from_cells(
                active_cells,
                source=source_name,
                sheet=sheet.name,
                row=row.index,
            )

            cp_name = extract_counterparty_from_narration(narration)
            counterparty = (
                Party(
                    id=f"party:{re.sub(r'[^a-zA-Z0-9]+', '_', cp_name.lower())}",
                    name=cp_name,
                )
                if cp_name
                else None
            )

            transactions.append(
                Transaction(
                    id=f"txn:axis_bank_statement:{len(transactions) + 1}",
                    date=txn_date,
                    amount=amount,
                    direction=direction,
                    currency="INR",
                    narration=narration,
                    balance=balance_dec,
                    counterparty=counterparty,
                    provenance=provenance,
                )
            )

        account = (
            Account(
                id=f"acc:axis_bank_statement:{account_number or 'default'}",
                account_number=account_number or "UNKNOWN",
                currency="INR",
            )
            if account_number
            else None
        )

        holder = (
            Party(
                id=f"party:{re.sub(r'[^a-zA-Z0-9]+', '_', holder_name.lower())}",
                name=holder_name,
            )
            if holder_name
            else None
        )

        return BankStatement(
            id=f"stmt:axis_bank_statement:{account_number or 'default'}",
            account=account,
            holder=holder,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            currency="INR",
            transactions=transactions,
            provenance=Provenance(
                source=source_name, sheet=sheet.name, metadata={"extractor": self.name}
            ),
            metadata={"layout": "tabular", "synthesized": True},
        )

    def _extract_multiline(self, workbook: Workbook, source_name: str) -> BankStatement:
        sheet = workbook.sheets[0]

        # 1. Extract metadata (Holder and Account Number)
        holder_name = ""
        for row in sheet.rows[:10]:
            row_str = " ".join(
                str(c.value or "").strip() for c in row.cells if c.value is not None
            ).strip()
            if row_str and not any(
                k in row_str.lower()
                for k in ["joint holder", "customer id", "ifsc code", "statement"]
            ):
                holder_name = row_str
                break

        account_number = ""
        for row in sheet.rows[:20]:
            row_str = " ".join(
                str(c.value or "").strip() for c in row.cells if c.value is not None
            ).strip()
            if (
                "account" in row_str.lower()
                or "statement of axis account no" in row_str.lower()
            ):
                m = re.search(
                    r"(?:account\s*no|account|no)\s*:\s*([0-9A-Za-z]+)",
                    row_str,
                    re.IGNORECASE,
                )
                if m:
                    account_number = m.group(1)
                    break

        # 2. Extract Opening Balance
        opening_balance: Decimal | None = None
        for row in sheet.rows[:35]:
            row_str = " ".join(
                str(c.value or "").strip() for c in row.cells if c.value is not None
            ).strip()
            if "opening balance" in row_str.lower():
                parts = row_str.split("|")
                if len(parts) > 1:
                    opening_balance = parse_decimal(parts[1])
                else:
                    m = re.search(r"(\d[\d,]*\.\d{2})", row_str)
                    if m:
                        opening_balance = parse_decimal(m.group(1))
                break

        # 3. Group rows into blocks across all sheets
        blocks: list[list[Any]] = []
        current_block: list[Any] = []
        in_transactions = False

        for s in workbook.sheets:
            # We reset trans-detect state on sheet boundaries because page headers repeat.
            in_transactions = False
            for row in s.rows:
                row_str = " ".join(
                    str(c.value or "").strip() for c in row.cells if c.value is not None
                ).strip()

                if (
                    "++++ end of statement ++++" in row_str.lower()
                    or "legends :" in row_str.lower()
                ):
                    in_transactions = False
                    break

                if "tran date" in row_str.lower() and (
                    "particulars" in row_str.lower() or "chq" in row_str.lower()
                ):
                    in_transactions = True
                    continue

                if "opening balance" in row_str.lower():
                    in_transactions = True
                    continue

                if not in_transactions:
                    continue

                # Check if this row starts a new block
                is_date_start = False
                words = row_str.split()
                if words:
                    first_word = words[0]
                    if re.match(r"^\d{2}-\d{2}-\d{4}$", first_word) or re.match(
                        r"^\d{2}-\d{2}-\d{4}", row_str
                    ):
                        is_date_start = True

                if is_date_start:
                    if current_block:
                        blocks.append(current_block)
                    current_block = [row]
                elif current_block:
                    current_block.append(row)

        if current_block:
            blocks.append(current_block)

        # 4. Process blocks into Transaction models
        transactions: list[Transaction] = []
        previous_balance = opening_balance
        closing_balance = opening_balance

        for block in blocks:
            if not block:
                continue

            # Extract date
            first_row_str = " ".join(
                str(c.value or "").strip()
                for c in block[0].cells
                if c.value is not None
            ).strip()
            date_match = re.search(r"(\d{2}-\d{2}-\d{4})", first_row_str)
            txn_date = date_match.group(1) if date_match else ""
            if not txn_date:
                continue

            # Parse amounts from last row of the block
            last_row = block[-1]
            last_row_str = " ".join(
                str(c.value or "").strip()
                for c in last_row.cells
                if c.value is not None
            ).strip()

            amount_dec = None
            balance_dec = None
            parts = last_row_str.split("|")
            if len(parts) >= 2:
                balance_match = re.search(r"(\d[\d,]*\.\d{2})", parts[-1])
                if balance_match:
                    balance_dec = parse_decimal(balance_match.group(1))
                amount_match = re.search(r"(\d[\d,]*\.\d{2})", parts[-2])
                if amount_match:
                    amount_dec = parse_decimal(amount_match.group(1))
            else:
                decimals = re.findall(r"(\d[\d,]*\.\d{2})", last_row_str)
                if len(decimals) >= 2:
                    amount_dec = parse_decimal(decimals[-2])
                    balance_dec = parse_decimal(decimals[-1])
                elif len(decimals) == 1:
                    balance_dec = parse_decimal(decimals[0])

            # Determine direction & reconcile balance
            direction = TransactionDirection.DEBIT
            if balance_dec is not None:
                if previous_balance is not None:
                    diff = balance_dec - previous_balance
                    if diff > 0:
                        direction = TransactionDirection.CREDIT
                        if amount_dec is None:
                            amount_dec = diff
                    else:
                        direction = TransactionDirection.DEBIT
                        if amount_dec is None:
                            amount_dec = abs(diff)
                else:
                    # If opening balance was missing, guess direction from keywords and back-infer opening balance
                    direction = TransactionDirection.DEBIT
                    if any(
                        k in last_row_str.lower()
                        for k in ["int.pd", "interest", "credit", "cr"]
                    ):
                        direction = TransactionDirection.CREDIT
                    if amount_dec is not None:
                        if direction == TransactionDirection.CREDIT:
                            opening_balance = balance_dec - amount_dec
                        else:
                            opening_balance = balance_dec + amount_dec

                closing_balance = balance_dec
                previous_balance = balance_dec
            else:
                if amount_dec is None:
                    amount_dec = Decimal("0")

            # Clean and construct multi-line narration
            narration_parts = []
            for i, r in enumerate(block):
                row_str = " ".join(
                    str(c.value or "").strip() for c in r.cells if c.value is not None
                ).strip()
                if i == 0:
                    row_str = re.sub(r"^\d{2}-\d{2}-\d{4}\s*", "", row_str)

                if i == len(block) - 1:
                    row_parts = row_str.split("|")
                    if len(row_parts) >= 2:
                        first_part = row_parts[0].strip()
                        clean_first_part = first_part
                        if amount_dec is not None:
                            amt_str_1 = f"{amount_dec:.2f}"
                            amt_str_2 = str(amount_dec)
                            if (
                                first_part == amt_str_1
                                or first_part == amt_str_2
                                or re.match(r"^\d+[\d,]*\.\d{2}$", first_part)
                            ):
                                clean_first_part = ""
                        if clean_first_part:
                            narration_parts.append(clean_first_part)
                    else:
                        clean_last_row = row_str
                        for dec_val in re.findall(r"(\d[\d,]*\.\d{2})", row_str):
                            clean_last_row = clean_last_row.replace(dec_val, "")
                        clean_last_row = re.sub(r"\s+", " ", clean_last_row).strip()
                        if clean_last_row:
                            narration_parts.append(clean_last_row)
                else:
                    if row_str:
                        narration_parts.append(row_str)

            narration = " / ".join(p.strip() for p in narration_parts if p.strip())
            narration = re.sub(r"/+", "/", narration)
            narration = re.sub(r"\s*/\s*", "/", narration).strip()

            # Provenance
            active_cells = []
            for r in block:
                active_cells.extend(
                    [c.location for c in r.cells if c.value is not None]
                )

            provenance = Provenance.from_cells(
                active_cells,
                source=source_name,
                sheet=sheet.name,
                row=block[0].index,
            )

            # Extract counterparty name from cleaned narration
            cp_name = extract_counterparty_from_narration(narration)
            counterparty = (
                Party(
                    id=f"party:{re.sub(r'[^a-zA-Z0-9]+', '_', cp_name.lower())}",
                    name=cp_name,
                )
                if cp_name
                else None
            )

            transactions.append(
                Transaction(
                    id=f"txn:axis_bank_statement:{len(transactions) + 1}",
                    date=txn_date,
                    amount=amount_dec or Decimal("0"),
                    direction=direction,
                    currency="INR",
                    narration=narration,
                    balance=balance_dec,
                    counterparty=counterparty,
                    provenance=provenance,
                )
            )

        if transactions and transactions[-1].balance is not None:
            closing_balance = transactions[-1].balance

        account = (
            Account(
                id=f"acc:axis_bank_statement:{account_number or 'default'}",
                account_number=account_number or "UNKNOWN",
                currency="INR",
            )
            if account_number
            else None
        )

        holder = (
            Party(
                id=f"party:{re.sub(r'[^a-zA-Z0-9]+', '_', holder_name.lower())}",
                name=holder_name,
            )
            if holder_name
            else None
        )

        return BankStatement(
            id=f"stmt:axis_bank_statement:{account_number or 'default'}",
            account=account,
            holder=holder,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            currency="INR",
            transactions=transactions,
            provenance=Provenance(
                source=source_name, sheet=sheet.name, metadata={"extractor": self.name}
            ),
            metadata={"layout": "multiline_block", "synthesized": True},
        )
