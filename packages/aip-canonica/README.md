# Canonica: Deterministic Document Extraction Framework

---

## 📌 Overview

Canonica is a stateless, deterministic document extraction framework designed for processing financial and structured data documents. It supports zero AI calls during runtime, relying on structured anchor-based extraction for speed and consistency. AI is used **only for offline learning** to discover new document layouts.

---

## 📦 What is Canonica?

Canonica is a framework that:

- **Extracts structured data** from documents (e.g., bank statements, invoices).
- **Uses anchor-based matching** to dynamically adapt to layout changes.
- **Records full provenance** for every extracted entity.
- **Supports deterministic execution** with zero LLM calls during runtime.
- **Leverages AI for offline learning** to discover and promote new document extractors.

---

## ❌ What is NOT Canonica?

- **No state management**: It does not store data or manage databases.
- **No runtime AI**: AI is used **only for learning**, not during execution.
- **No document layout assumptions**: It adapts dynamically to layout variations.

---

## 📄 Supported Document Types

Canonica currently supports:

- **Bank Statements**
- **Invoices**
- **Receipts**
- **Other structured documents** (via custom extractors)

---

## 📦 Public API

Canonica provides a simple API for extraction and testing:

```python
from aip_canonica.models import BankStatement
from aip_canonica.extractors import register_extractor

class CustomBankExtractor:
    @property
    def document_type(self) -> DocumentType:
        return DocumentType.BANK_STATEMENT

    @property
    def name(self) -> str:
        return "custom_bank"

    def matches(self, workbook: Workbook) -> bool:
        # Structural anchor check
        return any("custom bank" in str(c.value).lower() for s in workbook.sheets for r in s.rows[:10] for c in r.cells)

    def extract(self, workbook: Workbook, *, source_name: str = "") -> BankStatement:
        # Implementation here
        ...

register_extractor(CustomBankExtractor())
```

---

## 🔗 Graph Representation

Canonica supports full graph traversal and serialization:

```python
doc = understand("s3://financial-vault/2026/icici_statement.xlsx")

# Traverse graph
target_parties = graph.target_nodes(doc.id, relation="holder")

# Serialize
graph_dict = graph.to_dict()
```

---

## 🧾 First-Class Provenance

Every extracted entity records its origin with full traceability:

```python
txn = doc.transactions[0]
print(txn.provenance.sheet)    # 'Sheet0'
print(txn.provenance.row)      # 18
print(txn.provenance.source)   # 's3://financial-vault/2026/icici_statement.xlsx'
```

Provenance integrates directly with `aip_utils`:

```python
utils_prov = txn.provenance.to_utils_provenance()
```

---

## ⏱️ Deterministic Execution

Canonica ensures fast, deterministic execution through:

1. **Applicability Matching**: Extractors use structural anchors to determine if they can process a document.
2. **Anchor-Based Extraction**: Extractors adapt to layout changes without relying on fixed positions.
3. **Zero AI Calls**: Runtime uses pre-registered extractors for sub-millisecond execution.

---

## 🤖 Optional AI Learning

AI is used **only for offline learning** to discover new document layouts:

```text
Unknown Document Family
         │
         ▼
  StrategyLearner (uses aip-provider AI / Gemini 3.8 Flash)
         │
         ├─► New institution: Synthesizes initial layout extractor
         └─► Existing institution: Evolves extractor into unified class
         │
         ▼
  Candidate Extractor (.canonica/generated/)
         │
         ▼
  Autonomous Promotion Engine (thread-safe & process-safe)
         │
         ▼
  Promoted to aip_canonica/extractors/<category> & registered in registry.py
         │
         ▼
  Future Documents Execute Deterministically (0 AI calls, <10ms)
         │
         ▼
  Hourly Upstream Sync Job (verifies tests, creates feature branch, pushes to GitHub)
```

---

## 🧪 CLI Verification & Autonomous Learning

Verify documents or learn new layouts via CLI:

```bash
# 1. Deterministic verification (0 AI calls)
uv run python scripts/verify_canonica.py --file statement.pdf

# 2. Autonomous learning with AI (Gemini or Local Ollama)
uv run python scripts/verify_canonica.py --file statement.pdf --learn --provider gemini

# 3. End-to-end learning, promotion, and registration
uv run python scripts/verify_canonica.py --file statement.pdf --learn --provider gemini --promote

# 4. Upstream Git sync (safe, test-driven)
uv run python scripts/sync_extractors_to_upstream.py --dry-run
uv run python scripts/sync_extractors_to_upstream.py --remote origin
```

---

## 📁 Programmatic Promotion & Upstream Sync

Promote extractors and sync to upstream safely:

```python
from pathlib import Path
from aip_canonica.promotion import promote_extractor
from aip_canonica.publishing import sync_to_upstream

# Thread-safe promotion
target_file = promote_extractor(
    source_path=".canonica/generated/axis_bank_statement_extractor.py",
    category="bank",
    auto_register=True,
)

# Sync to upstream
result = sync_to_upstream(repo_root=Path("."), remote="origin")
```

---

## 🌐 Stateless Execution

Canonica is completely stateless:

- No databases or local file storage.
- File persistence is managed by the host application (e.g., S3, GCS, Blob storage).

Provenance source is preserved at all levels:

```python
doc = understand("s3://financial-vault/2026/icici_statement.xlsx")
print(doc.transactions[0].provenance.source)  # 's3://financial-vault/2026/icici_statement.xlsx'
```

---

## 🛠️ Adding a New Document Extractor

Implement the `Extractor` protocol:

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
        # Structural anchor check
        return any("custom bank" in str(c.value).lower() for s in workbook.sheets for r in s.rows[:10] for c in r.cells)

    def extract(self, workbook: Workbook, *, source_name: str = "") -> BankStatement:
        # Implementation here
        ...

register_extractor(CustomBankExtractor())
```

---

## 🔍 Running Tests

From the workspace root:

```bash
uv sync --all-packages
uv run pytest
```

For linting and type checking:

```bash
uv run ruff check packages/aip-canonica
uv run mypy --ignore-missing-imports packages/aip-canonica/src
```

---

## ✅ Conclusion

Canonica provides a robust, deterministic, and scalable solution for structured document extraction. It supports full provenance tracking, zero AI runtime calls, and AI-driven learning for continuous improvement.