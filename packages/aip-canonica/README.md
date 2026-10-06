# `aip-canonica` - Deterministic Document Extraction Engine

---

## 📌 Overview

**`aip-canonica`** is a stateless, zero-dependency document extraction engine built on the **`aip`** platform. It enables deterministic, anchor-based extraction of structured data from financial, banking, and business documents, with optional AI-powered learning for new document layouts.

---

## 📦 What is `aip-canonica`?

- **Deterministic Execution**: No AI or LLM queries during runtime.
- **Provenance Tracking**: Every extracted field and transaction records its source (sheet, row, column).
- **Graph-Based Representation**: Extracted data is modeled as a graph with full serialization support.
- **Stateless Architecture**: No databases, file storage, or cloud vaults are managed by the engine.

---

## ❌ What `aip-canonica` Is *Not*

- **Not a Document Store**: File persistence is handled by the host application (e.g., S3, GCS).
- **Not a Rule Engine**: Extractors are implemented via code, not declarative rules.
- **Not a General-Purpose Parser**: Optimized for structured financial and business documents.

---

## 📄 Supported Document Types

| Type | Description |
|------|-------------|
| `BANK_STATEMENT` | Extracts account details, transactions, and balances |
| `INVOICE` | Parses supplier, customer, itemized line items, and totals |
| `RECEIPT` | Identifies merchant, date, amount, and itemized purchases |
| `CUSTOM` | Use `Extractor` protocol to implement custom layouts |

---

## 🧰 Public API

```python
from aip_canonica.models import BankStatement, DocumentType
from aip_canonica.extractors import register_extractor, Extractor
from aip_canonica.utils import Workbook

# Example: Custom Bank Statement Extractor
class CustomBankExtractor(Extractor):
    @property
    def document_type(self) -> DocumentType:
        return DocumentType.BANK_STATEMENT

    @property
    def name(self) -> str:
        return "custom_bank"

    def matches(self, workbook: Workbook) -> bool:
        # Structural anchor check
        return any("custom bank" in str(c.value).lower()
                   for sheet in workbook.sheets
                   for row in sheet.rows[:10]
                   for cell in row.cells)

    def extract(self, workbook: Workbook, source_name: str = "") -> BankStatement:
        # Implement logic to extract fields and transactions
        return BankStatement(...)

# Register with global registry
register_extractor(CustomBankExtractor())
```

---

## 🔗 Graph-Based Representation

Extracted data is modeled as a graph with fully serializable nodes and edges.

```python
doc = understand("s3://vault/2026/icici.xlsx")

# Query graph nodes
target_parties = doc.graph.target_nodes(doc.id, relation="holder")

# Serialize graph
graph_dict = doc.graph.to_dict()

# Retrieve node by ID
node = doc.graph.get_node("txn_123")
```

---

## 🧾 First-Class Provenance

Every entity tracks its origin in the source document.

```python
txn = doc.transactions[0]

# Source tracking
print(txn.provenance.source)  # "s3://vault/2026/icici.xlsx"
print(txn.provenance.sheet)   # "Sheet0"
print(txn.provenance.row)     # 18
print(txn.provenance.cells)   # [CellLocation(...), ...]
```

---

## ⚙️ Deterministic Execution

1. **Applicability Check**: Extractors run `.matches(workbook)` to verify structural anchors.
2. **Anchor-Based Extraction**: Uses header labels, column headers, and stable patterns.
3. **Zero AI Calls**: Runs in milliseconds for known document families.

---

## 🤖 Optional AI Learning (Offline Only)

Used to discover new layouts, not for runtime execution.

```text
Unknown Document Family
         │
         ▼
  StrategyLearner (Gemini 3.8 Flash)
         │
         ├─ New Institution: Generate initial extractor
         └─ Existing Institution: Evolve to multi-layout class
         │
         ▼
  Candidate Extractor (.canonica/generated/)
         │
         ▼
  Promotion Engine (Thread-safe & Process-safe)
         │
         ▼
  Promoted to aip_canonica/extractors/<category>
         │
         ▼
  Hourly Sync Job: Pushes to GitHub
```

---

## 🚀 CLI Commands

### 1. Deterministic Verification
```bash
uv run python scripts/verify_canonica.py --file statement.pdf
```

### 2. AI-Powered Learning
```bash
uv run python scripts/verify_canonica.py --file statement.pdf --learn --provider gemini
```

### 3. End-to-End Learning & Promotion
```bash
uv run python scripts/verify_canonica.py --file statement.pdf --learn --provider gemini --promote
```

### 4. Upstream Git Sync
```bash
uv run python scripts/sync_extractors_to_upstream.py --dry-run
uv run python scripts/sync_extractors_to_upstream.py --remote origin
```

---

## 📁 Programmatic Promotion & Sync

```python
from pathlib import Path
from aip_canonica.promotion import promote_extractor
from aip_canonica.publishing import sync_to_upstream

# Safely promote a generated extractor
target_file = promote_extractor(
    source_path=".canonica/generated/axis_bank_statement_extractor.py",
    category="bank",
    auto_register=True,
)

# Sync promoted extractors to remote
result = sync_to_upstream(
    repo_root=Path("."),
    remote="origin",
    dry_run=False,
    force_push=False
)
```

---

## 🧪 Running Tests

From workspace root:

```bash
uv sync --all-packages
uv run pytest packages/aip-canonica
```

For lint and type-checking:

```bash
uv run ruff check packages/aip-canonica
uv run mypy --ignore-missing-imports packages/aip-canonica/src
```

---

## ✅ Best Practices

- **Extractor Design**: Focus on structural anchors, not fixed row numbers.
- **Provenance**: Always preserve the source URI for auditability.
- **Testing**: Use synthetic data and real-world documents to validate extractors.

---

## 📌 License

MIT License — See [LICENSE](LICENSE) for details.

---

This version improves readability with structured formatting, aligns with the updated AI learning flow, and enhances code examples with clear comments and parameters. It also reorganizes sections for better navigation and consistency.