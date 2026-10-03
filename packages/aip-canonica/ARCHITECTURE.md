# Canonica Architecture

## 1. Architectural Scope & Boundary

Canonica converts physical financial documents into strongly typed canonical representations that can participate in directed graphs.

```text
Physical Document (Excel, CSV)
             │
             ▼
     Document Parser
             │
             ▼
      Raw Workbook
             │
             ▼
     Extractor Registry
             │
             ├── [matches()]
             │
             ▼
     Layout Extractor
             │
             ▼
  Canonical Document / Graph
             │
             ├── [.validate()]
             └── [.as_graph()]
```

### System Boundaries
- **In Scope**:
  - Raw physical parsing (Excel via `openpyxl`, CSV via standard library).
  - Anchor-based matching and layout extraction.
  - Generic, typed canonical financial models (`BankStatement`, `Ledger`, `Invoice`, `InterestCertificate`, `TDSCertificate`).
  - Graph node and directed relationship construction.
  - First-class provenance tracking (cells, rows, lines).
  - Deterministic financial reconciliation.
  - Offline, isolated AI-assisted layout strategy learning via `aip-provider`.
- **Out of Scope**:
  - Graph database storage / querying.
  - Cross-document entity and account identity resolution.
  - Legal, circular, or regulatory compliance rules engines.
  - Heavyweight OCR or layout machine-learning models.

---

## 2. Component Architecture

### A. Source & Parser Layer (`aip_canonica.parsers`)
Adapts physical file formats into an in-memory tabular structure (`Workbook`, `Sheet`, `Row`, `Cell`, `CellLocation`).
- `DocumentParser`: Base abstraction for parsing file paths.
- `ExcelParser`: Loads `.xlsx` / `.xls` via `openpyxl`.
- `CsvParser`: Loads delimited files with dialect sniffing, handling varied line breaks, quotes, and encoding.
- `ExtractorRegistry`: Dispatches parsing strategies based on file extension and document type.

### B. Canonical Model & Graph Layer (`aip_canonica.models`)
- `CanonicalNode` (Protocol): Base interface for all graph entities, defining required attributes such as `id`, `node_type`, `provenance`, and `to_dict()`.
- `CanonicalDocument` (Protocol): Top-level interface for document models, requiring implementation of `.as_graph()` and `.validate()`.
- `CanonicalGraph`: In-memory representation of a directed graph, supporting operations like:
  - Outgoing relationship discovery (`graph.outgoing(node_id)`)
  - Incoming relationship discovery (`graph.incoming(node_id)`)
  - Target resolution (`graph.resolve(target_id)`)
- `Relationship`: Directed edge in the graph, with fields:
  - `source_id`: ID of the source node
  - `target_id`: ID of the target node
  - `relation`: Semantic relationship type (e.g., "issuer", "contains")
  - `properties`: Additional metadata (e.g., transaction amount, date)
- **Domain Models**:
  - **Banking**: `BankStatement`, `Transaction`
  - **Invoicing**: `Invoice`, `InvoiceLine`, `Tax`, `Discount`
  - **Accounting**: `Ledger`, `LedgerEntry`
  - **Certificates**: `InterestCertificate`, `TDSCertificate`, `TDSEntry`
  - **Entities**: `Party`, `Account`, `DatePeriod`, `Money`

### C. Extractor Layer (`aip_canonica.extractors`)
Converts physical workbooks into canonical documents deterministically.
- `Extractor` (Protocol): Interface for document extractors, requiring:
  - `name`: Human-readable name of the extractor
  - `document_type`: Type of document this extractor supports (e.g., "bank-statement")
  - `matches(workbook)`: Function to determine if this extractor applies to a given workbook
  - `extract(workbook)`: Function to convert a workbook into a canonical document
- `ExtractorRegistry`: Manages registered extractors and selects the appropriate one for a given workbook.
- **Built-in Extractors**:
  - `ICICIBankStatementExtractor`: Handles complex ICICI bank statements with multi-column layouts, dynamic row offsets, metadata blocks, and summary footers.
  - `StandardBankStatementExtractor`: Processes standard bank statements in CSV and Excel formats with uniform layouts.
  - `TabularInvoiceExtractor`: Parses tabular invoices containing lines, taxes, and discounts.
  - `TabularLedgerExtractor`: Processes general and sub-ledger entries in structured formats.

### D. Validation Layer (`aip_canonica.validation`)
- `ValidationResult`: Container for validation results, including success/failure status and detailed messages.
- `ValidationIssue`: Structured representation of individual validation errors, including:
  - `code`: Error code
  - `message`: Human-readable description
  - `location`: Source of the error (e.g., cell reference)
- `BankStatementValidator`: Ensures consistency in bank statements by verifying that `opening_balance + total_credits - total_debits ≈ closing_balance`.
- `InvoiceValidator`: Validates that invoice totals match the sum of line items, taxes, and discounts.
- `LedgerValidator`: Confirms that ledger balances are consistent with `opening_balance + debits - credits ≈ closing_balance`.
- `validate()`: Central validation function that orchestrates document-specific validation rules.

### E. AI Learning Layer (`aip_canonica.learning`)
- **Isolation Principle**: Completely decoupled from deterministic runtime execution to ensure separation of concerns and prevent unintended side effects.
- `StrategyLearner`: AI component that interacts with `aip_provider.AI` to analyze document samples and derive extraction strategies for unknown layouts.
- **Output**: `LearnedStrategy` object, which encapsulates:
  - Extractor configuration parameters
  - Layout-specific rules
  - Mapping instructions for data fields
  - These strategies can be converted into executable extractors via the `ExtractorFactory`.

---

## 3. Graph Data Model & Traversal

Canonical documents provide `.as_graph()`, which constructs a directed graph of nodes and relationships:

```text
Invoice (inv:INV-001)
  ├── relation: "issuer" ──────> Party (party:gstin:29ABC...)
  ├── relation: "recipient" ───> Party (party:gstin:27XYZ...)
  └── relation: "contains" ────> InvoiceLine (line:1)
                                      └── relation: "tax" ──> Tax (tax:line:1)
```

### Incoming Relationship Discovery
Incoming relationships allow client applications to trace all documents or lines that reference a specific entity. For example:

```python
incoming_edges = graph.incoming("party:gstin:29ABC...")
# -> [Relationship(source_id="inv:INV-001", relation="issuer", target_id="party:gstin:29ABC...")]
```

This feature enables powerful query capabilities such as:
- Finding all invoices issued by a specific party
- Locating all ledger entries related to a particular account
- Identifying all tax lines associated with a given invoice line

---

## 4. Provenance Tracking

Every entity in the system carries a `Provenance` object that tracks its origin and context:

- `source`: File path or document identifier (e.g., `/data/invoices/2023/Q3/INV-001.xlsx`)
- `sheet`: Name of the Excel sheet or worksheet (e.g., "Invoice Details")
- `row`, `column`, `address`: Exact location in the document (e.g., `B145` for row 145, column B)
- `cells`: Tuple of `CellLocation` records providing detailed metadata for each relevant cell

This provenance information is interoperable with `aip_utils.Provenance`, enabling integration with other systems for audit trails, data lineage tracking, and debugging purposes.