# Canonica

> Convert heterogeneous financial documents into a finite set of generic, strongly typed canonical financial representations and directed graphs.

Canonica is intentionally a lightweight library for financial document understanding.

```python
from aip_canonica import understand

statement = understand("icici_statement.xlsx")
print(statement.closing_balance)
print(f"Extracted {len(statement.transactions)} transactions")

# Graph representation with relationship discovery
graph = statement.as_graph()
outgoing = graph.outgoing(statement.id)
incoming = graph.incoming(statement.account.id)
```

---

## 1. What Canonica Is

Canonica converts unstructured or semi-structured business and financial documents (Excel, CSV, PDF, tabular sheets) into strongly typed canonical financial models.

Its primary boundary is:
```text
Document  ──>  Canonical financial object / graph
```

- **Strongly Typed**: Python 3.12 dataclasses with strict slots and type annotations.
- **Graph Compatible**: Documents and entities participate as nodes in a small, directed relationship graph with incoming and outgoing relationship discovery.
- **First-Class Provenance**: Every extracted entity traces back to its source location (cells, rows, lines).
- **Deterministic Runtime**: Known document layouts execute with **0 AI / LLM calls**.
- **Deterministic Validation**: Mathematical reconciliation rules (e.g. `opening + deposits - withdrawals ≈ closing`).

## 2. What Canonica is NOT

To keep Canonica modular and maintainable, it intentionally stops at the document boundary. Canonica is **NOT**:

- A knowledge graph database
- A client/account resolution system
- An entity-resolution engine
- A regulatory rules engine
- A RAG system
- An OKF implementation
- An OCR framework
- A generic financial data warehouse
- An agent framework

Those belong in higher-level application layers consuming Canonica objects.

---

## 3. Supported Canonical Document Types

Canonica supports a finite set of initial canonical financial document types:

| Document Type | Description | Key Extracted Fields |
|---|---|---|
| **BankStatement** | Bank account movement statement | Statement identity, Account, Holder, Financial Institution, Period, Opening/Closing Balances, Transactions |
| **Ledger** | General ledger or sub-ledger statement | Ledger identity/name, Account, Party, Period, Opening/Closing Balances, Ledger Entries |
| **Invoice** | Generic sales or purchase invoice | Invoice number, Issuer Party, Recipient Party, Dates, Line items, Taxes, Discounts, Totals |
| **InterestCertificate** | Interest certificate from bank/institution | Institution, Recipient, Account, Period, Interest Amount, TDS Deducted |
| **TDSCertificate** | TDS Certificate (e.g., Form 16/16A) | Certificate number, Deductor, Deductee, Financial/Assessment Year, Total Paid, Total Tax Deducted, TDS Entries |

> **Note on Invoices**: Canonica provides **ONE** generic `Invoice` model. It does not differentiate `SaleInvoice` and `PurchaseInvoice`, because that interpretation belongs to the consuming client layer.

---

## 4. Public API

Canonica exposes a tiny public surface:

```python
from aip_canonica import understand, validate, parse_document

# 1. Deterministic conversion
document = understand("statement.xlsx")

# 2. Deterministic conversion with strict validation enforcement
document = understand("statement.xlsx", validate=True)

# 3. Inspect deterministic reconciliation
result = validate(document)
assert result.is_valid

# 4. Low-level physical workbook parsing (if needed)
workbook = parse_document("statement.xlsx")
```

---

## 5. Graph-Compatible Representation

Canonical models are not merely nested Python objects; they can form a small directed graph where entities are nodes and connections are directed relationships:

```text
Invoice
  ├── issuer ──────> Party
  ├── recipient ───> Party
  ├── contains ────> InvoiceLine ── tax ──> Tax
  ├── tax ─────────> Tax
  └── discount ────> Discount

BankStatement
  ├── account ─────> Account
  ├── holder ──────> Party
  ├── institution ─> Party
  └── contains ────> Transaction ── counterparty ──> Party
```

### Discovering Outgoing and Incoming Relationships

Every canonical document implements `.as_graph() -> CanonicalGraph`:

```python
graph = statement.as_graph()

# Outgoing relationships from the statement
for rel in graph.outgoing(statement.id):
    print(f"{statement.id} --[{rel.relation}]--> {rel.target_id}")

# Incoming relationships (e.g. find all documents referencing this account)
incoming = graph.incoming(statement.account.id)
for rel in incoming:
    print(f"Source {rel.source_id} references account via '{rel.relation}'")

# Direct node retrieval
target_parties = graph.target_nodes(statement.id, relation="holder")
```

The graph is fully serializable:
```python
graph_dict = graph.to_dict()
```

---

## 6. First-Class Provenance

Every extracted entity records exactly where its data originated.

```python
txn = statement.transactions[0]
print(txn.provenance.sheet)    # 'Sheet0'
print(txn.provenance.row)      # 18
print(txn.provenance.cells)    # (CellLocation(sheet='Sheet0', row=18, column=1, address='A18'), ...)
```

Provenance integrates directly with the platform's `aip_utils`:
```python
utils_prov = txn.provenance.to_utils_provenance()
```

---

## 7. Deterministic Execution & Same-Family Reuse

Runtime execution is 100% deterministic:
1. **Applicability Match**: When a document is provided, registered extractors run `.matches(workbook)` to verify structural anchors before extraction begins.
2. **Anchor-Based Extraction**: Extractors do NOT depend on fixed row numbers or transaction counts. They identify stable structural anchors (header labels, table columns) and adapt dynamically if rows shift.
3. **Zero AI Calls**: Known document families run in milliseconds with zero LLM queries.

---

## 8. Optional AI Learning

Canonica uses AI exclusively for **offline learning** to discover new document layouts, never for routine runtime execution:

```text
Unknown Document Family
         │
         ▼
  StrategyLearner (uses aip-provider AI)
         │
         ▼
  LearnedStrategy (structural anchors, column mappings)
         │
         ▼
  Register Extractor
         │
         ▼
  Future Documents Execute Deterministically (0 AI calls)
```

Learning uses `aip-provider` directly:

```python
from aip_canonica.learning import StrategyLearner
from aip_provider import AI

learner = StrategyLearner(ai=AI.local())
strategy = await learner.learn_from_workbook(workbook, name="coop_bank")
```

---

## 9. Stateless Execution & Document Provenance

Canonica is completely stateless: it does not manage databases, local file retention, or cloud storage vaults. File persistence belongs to the host application (e.g., S3, GCS, Blob storage, or local disk).

Canonica records the caller-supplied file path or URI directly into the canonical document's `provenance.source` and propagates it to every child line item and transaction:

```python
doc = understand("s3://financial-vault/2026/icici_statement.xlsx")

# Document-level provenance
print(doc.provenance.source)  # "s3://financial-vault/2026/icici_statement.xlsx"

# Granular entity-level provenance
print(doc.transactions[0].provenance.source)  # Exact origin preserved
print(doc.transactions[0].provenance.row)     # Original sheet row index
```

---

## 10. How to Add a New Document Extractor

Adding a new document layout requires implementing the `Extractor` protocol:

```python
from aip_canonica.extractors import Extractor, register_extractor
from aip_canonica.models import BankStatement, DocumentType, Workbook

class CustomBankExtractor:
    @property
    def document_type(self) -> DocumentType:
        return DocumentType.BANK_STATEMENT

    @property
    def name(self) -> str:
        return "custom_bank"

    def matches(self, workbook: Workbook) -> bool:
        # Check structural anchors
        return any("custom bank" in str(c.value).lower() for s in workbook.sheets for r in s.rows[:10] for c in r.cells)

    def extract(self, workbook: Workbook, *, source_name: str = "") -> BankStatement:
        # Deterministically extract fields and transactions
        ...
        return BankStatement(...)

# Register with the global registry
register_extractor(CustomBankExtractor())
```

---

## 10. Running Tests

From the workspace root:

```bash
uv sync --all-packages
uv run pytest
```

To run lint and type checking:

```bash
uv run ruff check packages/aip-canonica
uv run mypy --ignore-missing-imports packages/aip-canonica/src
```