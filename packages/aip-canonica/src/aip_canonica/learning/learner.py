# Canonica AI Strategy Learning Report: Sample Bank Statement Extraction

- **Detected Document Type**: `BANK_STATEMENT`
- **Layout Paradigm**: `TABULAR`
- **Evolution Action**: `REINFORCEMENT`
- **Target Institution Extractor**: `ICICI_Bank_Extractor`
- **Recommendation**: `IMPLEMENT_GENERATED_EXTRACTOR`
- **Generated Extractor File**: [bank_extractor.py](file:///path/to/bank_extractor.py)

---

## 1. Discovered Structural Anchors & Table Headers
- **Anchor Keywords**: `account number`, `transaction date`, `closing balance`
- **Table Header Keywords**: `date`, `description`, `debit`, `credit`, `balance`

## 2. Layout Delimiters & Multi-Line Rules
| Delimiter / Pattern | Value |
| :--- | :--- |
| `page total` | `Breaks transaction listing` |
| `closing balance` | `Ends transaction table` |
| `unless otherwise stated` | `Excludes special cases` |

## 3. Discovered Column Mappings
| Canonical Field | Document Header / Label |
| :--- | :--- |
| `date` | `txn_date` |
| `description` | `particulars` |
| `debit` | `withdrawal` |
| `credit` | `deposit` |
| `balance` | `bal` |

## 4. Discovered Metadata Fields
| Field | Label / Source in Document |
| :--- | :--- |
| `account_number` | `Account No: 123456789` |
| `holder_name` | `Name: John Doe` |

## 5. Metadata Density Comparison
- **Standard Baseline Extracted Fields**: `date`, `amount`, `balance`
- **AI Discovered Metadata Fields**: `description`, `counterparty`, `transaction_type`
- **Richer Metadata Fields**: `account_number`, `holder_name`, `currency`, `institution`

## 6. Layout Observations & Evolution Rationale
The document uses a tabular layout with consistent column alignment. The header row is typically found within the first 4 rows, and metadata is often located above the transaction table. The use of "Account No" and "Name" patterns reliably identifies account information. The extractor was evolved to handle multi-word headers like "Transaction Date" and "Particulars" for improved accuracy.

## 7. Generated Extractor Implementation Code
```python
class ICICI_Bank_Extractor(Strategy):
    name = "ICICI_Bank_Extractor"
    layout_type = "tabular"
    document_type = DocumentType.BANK_STATEMENT
    column_mapping = {
        "date": "txn_date",
        "description": "particulars",
        "debit": "withdrawal",
        "credit": "deposit",
        "balance": "bal"
    }
    metadata_fields = {
        "account_number": "Account No",
        "holder_name": "Name"
    }
    anchor_keywords = ["account number", "transaction date", "closing balance"]
    block_delimiters = {
        "page_total": "Page Total",
        "closing_balance": "Closing Balance",
        "unless": "Unless Otherwise Stated"
    }

    def matches(self, workbook: Workbook) -> bool:
        anchors = {"account number", "transaction date", "closing balance"}
        headers = {"date", "description", "debit", "credit", "balance"}
        for sheet in workbook.sheets:
            for row in sheet.rows[:35]:
                row_text = " ".join(str(c.value or "").lower() for c in row.cells if c.value is not None)
                if any(a.lower() in row_text for a in anchors):
                    return True
                if all(h.lower() in row_text for h in headers[:3]):
                    return True
        return False

    def extract(self, workbook: Workbook, *, source_name: str = "") -> BankStatement:
        sheet = workbook.sheets[0]
        col_map = {
            "date": 0,
            "description": 2,
            "debit": 3,
            "credit": 4,
            "balance": 5
        }

        # Locate header row
        header_row_idx = None
        for row in sheet.rows[:40]:
            row_texts = [str(c.value or "").strip().lower() for c in row.cells if c.value is not None]
            matches_count = 0
            for canonical_key, doc_header in self.column_mapping.items():
                if any(doc_header.lower() in t for t in row_texts):
                    matches_count += 1
            if matches_count >= 2:
                header_row_idx = row.index
                for c_idx, cell in enumerate(row.cells):
                    txt = str(cell.value or "").strip().lower()
                    for canonical_key, doc_header in self.column_mapping.items():
                        if doc_header.lower() in txt or txt in doc_header.lower():
                            col_map[canonical_key] = c_idx
                break

        if header_row_idx is None:
            raise ValueError("Could not locate table header in ICICI Bank layout.")

        # Extract metadata
        account_number = ""
        holder_name = ""
        for row in sheet.rows[:header_row_idx]:
            for cell in row.cells:
                val = str(cell.value or "").strip()
                if "account" in val.lower() and not account_number:
                    m = re.search(r"(?:a/c|account|no)[^0-9]*([0-9A-Za-z]+)", val, re.IGNORECASE)
                    if m:
                        account_number = m.group(1)
                if "name" in val.lower() and not holder_name:
                    m = re.search(r"name\\s*[:-]+\\s*(.+)", val, re.IGNORECASE)
                    if m:
                        holder_name = m.group(1)

        # Extract transactions
        transactions = []
        opening_balance = None
        closing_balance = None

        for row in sheet.rows:
            if row.index <= header_row_idx:
                continue

            row_str = " ".join(str(c.value or "").strip() for c in row.cells if c.value is not None)
            if not row_str or any(stop in row_str.lower() for stop in ["page total", "closing balance", "legend", "unless otherwise stated"]):
                break

            try:
                date = str(row.cells[col_map["date"]].value or "").strip()
                description = str(row.cells[col_map["description"]].value or "").strip()
                debit = float(row.cells[col_map["debit"]].value or 0)
                credit = float(row.cells[col_map["credit"]].value or 0)
                balance = float(row.cells[col_map["balance"]].value or 0)
            except (ValueError, IndexError):
                continue

            if debit > 0:
                transaction_type = "DEBIT"
            elif credit > 0:
                transaction_type = "CREDIT"
            else:
                transaction_type = "BALANCE"

            transactions.append({
                "date": date,
                "description": description,
                "debit": debit,
                "credit": credit,
                "balance": balance,
                "type": transaction_type
            })

            if opening_balance is None:
                opening_balance = balance
            closing_balance = balance

        return BankStatement(
            account_number=account_number,
            holder_name=holder_name,
            transactions=transactions,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            currency="INR",
            institution="ICICI Bank"
        )
```

---

This report demonstrates a complete example of how the `generate_detailed_markdown_report` function would generate documentation for a learned strategy. The example includes:

1. **Document metadata**: Type, layout, evolution action, and recommendation.
2. **Structural elements**: Anchors, headers, and delimiters that define the document's layout.
3. **Field mappings**: How canonical fields are mapped to document headers.
4. **Metadata extraction**: How account and holder information is identified.
5. **Field comparison**: Baseline vs AI-discovered fields.
6. **Observations**: Notes on the document's layout and how the extractor was evolved.
7. **Generated code**: A complete implementation of the extractor class with all necessary logic.

This structure provides a clear template for documenting any learned strategy, ensuring consistency and completeness in the generated reports.