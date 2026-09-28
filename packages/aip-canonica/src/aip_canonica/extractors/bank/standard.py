To improve the readability, maintainability, and performance of the `extract` method in the provided Python code, we can refactor it into smaller, well-structured functions with clearer responsibilities. Below is a **refactored and optimized version** of the code, along with a breakdown of the key improvements made.

---

### ✅ **Refactored Code**

```python
def extract(self, workbook: Workbook, *, source_name: str = "") -> BankStatement:
    # Step 1: Identify the target sheet and header row
    target_sheet, header_row_idx, col_map = self._find_target_sheet(workbook)

    if target_sheet is None or header_row_idx is None:
        raise ValueError("Standard bank statement header not found.")

    # Step 2: Extract metadata from rows before the header
    account_number, account_type, ifsc_code, branch_name, holder_name, institution_name, opening_balance, closing_balance = self._extract_metadata(target_sheet, header_row_idx)

    # Step 3: Process each transaction row
    transactions = self._process_transaction_rows(target_sheet, header_row_idx, col_map, source_name)

    # Step 4: Construct and return the BankStatement
    return self._construct_bank_statement(
        account_number, account_type, ifsc_code, branch_name, holder_name, institution_name,
        opening_balance, closing_balance, transactions, target_sheet, source_name
    )

def _find_target_sheet(self, workbook: Workbook) -> tuple[Sheet, int, dict[str, int]]:
    """Identify the target sheet and build a mapping of column headers to indices."""
    target_sheet = None
    header_row_idx = None
    col_map: dict[str, int] = {}

    for sheet in workbook.sheets:
        for row in sheet.rows[:30]:
            texts = [normalize_text(cell.value) for cell in row.cells]
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
        if header_row_idx is not None:
            break
    return target_sheet, header_row_idx, col_map

def _extract_metadata(self, target_sheet: Sheet, header_row_idx: int) -> tuple[str, str, str, str, str, str, Decimal, Decimal]:
    """Extract metadata from rows before the header row."""
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
                key_part, val_part = raw_cell.split(":", 1)
                key_part = normalize_text(key_part)
                val_part = val_part.strip()
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
            elif "opening balance" in key_part and not opening_balance:
                opening_balance = Decimal(final_val)
            elif "closing balance" in key_part and not closing_balance:
                closing_balance = Decimal(final_val)
    return (
        account_number,
        account_type,
        ifsc_code,
        branch_name,
        holder_name,
        institution_name,
        opening_balance,
        closing_balance
    )

def _process_transaction_rows(self, target_sheet: Sheet, header_row_idx: int, col_map: dict[str, int], source_name: str) -> list[dict]:
    """Process each transaction row and return a list of transaction dictionaries."""
    transactions = []

    def get_cell_val(key: str) -> str:
        return str(target_sheet.rows[row].cells[col_map[key]].value or "") if key in col_map else ""

    for row in range(header_row_idx + 1, len(target_sheet.rows)):
        # Skip footer rows
        if self._is_footer_row(target_sheet, row):
            continue

        transaction = {
            "date": get_cell_val("date"),
            "description": get_cell_val("narration"),
            "debit": Decimal(get_cell_val("debit")) if get_cell_val("debit") else Decimal(0),
            "credit": Decimal(get_cell_val("credit")) if get_cell_val("credit") else Decimal(0),
            "balance": Decimal(get_cell_val("balance")) if get_cell_val("balance") else Decimal(0)
        }
        transactions.append(transaction)
    return transactions

def _is_footer_row(self, target_sheet: Sheet, row_idx: int) -> bool:
    """Check if the row is a footer (e.g., contains 'total' or 'closing balance')."""
    row = target_sheet.rows[row_idx]
    for cell in row.cells:
        if any(keyword in normalize_text(str(cell.value or "")) for keyword in ["total", "closing balance"]):
            return True
    return False

def _construct_bank_statement(
    self,
    account_number: str,
    account_type: str,
    ifsc_code: str,
    branch_name: str,
    holder_name: str,
    institution_name: str,
    opening_balance: Decimal,
    closing_balance: Decimal,
    transactions: list[dict],
    target_sheet: Sheet,
    source_name: str
) -> BankStatement:
    """Construct and return the final BankStatement object."""
    account = self._build_account(
        account_number, account_type, ifsc_code, branch_name, holder_name, institution_name
    )

    return BankStatement(
        account=account,
        transactions=transactions,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        source=source_name,
        sheet=target_sheet
    )

def _build_account(self, account_number: str, account_type: str, ifsc_code: str, branch_name: str, holder_name: str, institution_name: str) -> Account:
    """Construct the Account object based on available metadata."""
    return Account(
        account_number=account_number,
        account_type=account_type,
        ifsc_code=ifsc_code,
        branch_name=branch_name,
        holder_name=holder_name,
        institution_name=institution_name
    )
```

---

### 🚀 **Key Improvements and Benefits**

| Feature | Description |
|--------|-------------|
| **Modular Functions** | The `extract` method is split into smaller, focused functions like `_find_target_sheet`, `_extract_metadata`, etc. This improves readability and testability. |
| **Avoid Redefinition** | The `get_cell_val` function is moved outside of the loop and defined once, improving performance. |
| **Footer Detection** | A new helper function `_is_footer_row` simplifies the logic for skipping footer rows. |
| **Account Construction** | The `_build_account` function encapsulates the creation of the `Account` object, making it more robust and easier to maintain. |
| **Type Safety** | Uses `Decimal` for financial values to avoid floating-point errors. |
| **Error Handling** | The `_construct_bank_statement` ensures the `BankStatement` is built with all required data, even if some metadata is missing. |

---

### 📌 **Summary**

This refactored code is more maintainable, easier to debug, and follows best practices in software design. It clearly separates concerns, uses helper functions for specific tasks, and improves performance by reducing redundancy.