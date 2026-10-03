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
  - **Parsing**: Raw physical parsing (Excel via `openpyxl`, CSV via standard library).
  - **Extraction**: Anchor-based matching and layout extraction.
  - **Modeling**: Generic, typed canonical financial models (`BankStatement`, `Ledger`, `Invoice`, `InterestCertificate`, `TDSCertificate`).
  - **Graph Construction**: Graph node and directed relationship construction.
  - **Provenance**: First-class provenance tracking (cells, rows, lines).
  - **Validation**: Deterministic financial reconciliation.
  - **AI Learning**: Offline, isolated AI-assisted layout strategy learning via `aip-provider`.
- **Out of Scope**:
  - **Storage**: Graph database storage / querying.
  - **Identity Resolution**: Cross-document entity and account identity resolution.
  - **Compliance**: Legal, circular, or regulatory compliance rules engines.
  - **OCR/ML**: Heavyweight OCR or layout machine-learning models.

---

## 2. Component Architecture

### A. Source & Parser Layer (`aip_canonica.parsers`)
Adapts physical file formats into an in-memory tabular structure (`Workbook`, `Sheet`, `Row`, `Cell`, `CellLocation`).
- `DocumentParser`: Base abstraction for parsing file paths.
- `ExcelParser`: Loads `.xlsx` / `.xls` via `openpyxl`.
- `CsvParser`: Loads delimited files with dialect sniffing, handling varied line breaks, quotes, and empty rows.
- `ParserFactory`: Dispatches by file extension.

### B. Canonical Model & Graph Layer (`aip_canonica.models`)
- `CanonicalNode` (Protocol): Any entity participating in the financial graph (`id`, `node_type`, `provenance`, `to_dict()`).
- `CanonicalDocument` (Protocol): Top-level document models providing `.as_graph()` and `.validate()`.
- `CanonicalGraph`: An in-memory directed graph supporting outgoing discovery, incoming relationship discovery, and target resolution.
- `Relationship`: Directed edge with `source_id`, `relation`, `target_id`, `target_type`, and `properties`.
- **Domain Models**:
  - `BankStatement`, `Transaction`
  - `Invoice`, `InvoiceLine`, `Tax`, `Discount`
  - `Ledger`, `LedgerEntry`
  - `InterestCertificate`, `TDSCertificate`, `TDSEntry`
  - `Party`, `Account`, `DatePeriod`, `Money`

### C. Extractor Layer (`aip_canonica.extractors`)
Converts physical workbooks into canonical documents deterministically.
- `Extractor` (Protocol): Declares `name`, `document_type`, `matches(workbook)`, and `extract(workbook)`.
- `ExtractorRegistry`: Maintains known strategies and matches documents before extraction.
- **Built-in Extractors**:
  - `ICICIBankStatementExtractor`: Handles complex multi-column statements with dynamic row offsets, metadata blocks, and summary footers.
  - `StandardBankStatementExtractor`: Handles standard tabular bank movements across CSV and Excel.
  - `TabularInvoiceExtractor`: Handles tabular invoices with lines, taxes, and totals.
  - `TabularLedgerExtractor`: Handles general and sub-ledger movements.

### D. Validation Layer (`aip_canonica.validation`)
- `ValidationResult`, `ValidationIssue`: Structured, inspectable validation reports.
- `BankStatementValidator`: Reconciles `opening + total_credits - total_debits ≈ closing`.
- `InvoiceValidator`: Reconciles `lines + taxes - discounts ≈ total`.
- `LedgerValidator`: Reconciles `opening + debits - credits ≈ closing`.
- `validate()`: Top-level dispatcher.

### E. AI Learning Layer (`aip_canonica.learning`)
- **Isolation**: Operates independently of the main execution flow.
- `StrategyLearner`: Queries `aip_provider.AI` to inspect document samples and discover anchors and mappings for unknown layouts.
- **Output**: `LearnedStrategy`, which can be converted into an extractor.

---

## 3. Graph Data Model & Traversal

Canonical documents provide `.as_graph()`, populating nodes and directed edges:

```text
Invoice (inv:INV-001)
  ├── relation: "issuer" ──────> Party (party:gstin:29ABC...)
  ├── relation: "recipient" ───> Party (party:gstin:27XYZ...)
  └── relation: "contains" ────> InvoiceLine (line:1)
                                      └── relation: "tax" ──> Tax (tax:line:1)
```

### Incoming Relationship Discovery
Incoming relations allow client applications to discover all documents or lines referring to an entity:
```python
incoming_edges = graph.incoming("party:gstin:29ABC...")
# -> [Relationship(source_id="inv:INV-001", relation="issuer", target_id="party:gstin:29ABC...")]
```

---

## 4. Provenance Tracking

Every entity holds a `Provenance` object referencing:
- **Source**: File path or document identifier.
- **Sheet**: Sheet name.
- **Coordinates**: `row`, `column`, `address` (e.g. `B145`).
- **Cells**: Complete tuple of `CellLocation` records.
- **Interoperability**: Compatible with `aip_utils.Provenance` for consistent tracking across systems.