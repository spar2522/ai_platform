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
- `ExcelParser`: Loads `.xlsx` via `openpyxl` and legacy `.xls` via `xlrd`.
- `PdfParser`: Extracts digital vector text into sheet rows via `pypdf`/`pdfplumber`, with transparent multimodal AI recovery for scanned raster PDFs.
- `CsvParser`: Loads delimited files with dialect sniffing, handling varied line breaks, quotes, and empty rows.
- `ParserFactory`: Dispatches by file extension.

### B. Canonical Model & Graph Layer (`aip_canonica.models`)
- `CanonicalNode` (Protocol): Any entity participating in the financial graph (`id`, `node_type`, `provenance`, `to_dict()`).
- `CanonicalDocument` (Protocol): Top-level document models providing `.as_graph()` and `.validate()`.
- `CanonicalGraph`: An in-memory directed graph supporting outgoing discovery, incoming relationship discovery, and target resolution.
- `Relationship`: Directed edge with `source_id`, `relation`, `target_id`, `target_type`, and `properties`.
- Domain Models:
  - `BankStatement`, `Transaction`
  - `Invoice`, `InvoiceLine`, `Tax`, `Discount`
  - `Ledger`, `LedgerEntry`
  - `InterestCertificate`, `TDSCertificate`, `TDSEntry`
  - `Party`, `Account`, `DatePeriod`, `Money`

### C. Extractor Layer (`aip_canonica.extractors`)
Converts physical workbooks into canonical documents deterministically.
- `Extractor` (Protocol): Declares `name`, `document_type`, `matches(workbook)`, and `extract(workbook)`.
- `ExtractorRegistry`: Maintains known strategies and matches documents before extraction.
- Built-in extractors:
  - `AxisBankStatementExtractor`: Multi-layout unified extractor supporting both flat tabular spreadsheets (XLS) and wrapped multiline block layouts (PDF).
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
- Completely isolated from deterministic runtime execution.
- `StrategyLearner`: Queries `aip_provider.AI` (e.g. Gemini 3.8 Flash) to inspect document samples and discover anchors and mappings for unknown layouts.
- Multi-Layout Evolution: When a new document layout variant arrives for an existing institution, the learner evolves the existing extractor into a single unified class supporting both variants.
- Output: `LearnedStrategy` and synthesized Python code in `.canonica/generated/`.

### F. Autonomous Promotion Engine (`aip_canonica.promotion`)
- Concurrency-Safe Installation: Uses `threading.RLock()` and OS-level `fcntl.flock` on `extractors/.promotion.lock` to guarantee thread safety and process safety across web service workers.
- AST Class Detection: Automatically identifies the primary `Extractor` class in the synthesized file.
- Automated Wiring: Copies code into `aip_canonica/extractors/<category>/`, registers imports and instantiations in `registry.py`, and runs `ruff` format and linting.

### G. Upstream Synchronization (`aip_canonica.publishing`)
- Decoupled Batch Execution: Operates independently from the request processing path via `scripts/sync_extractors_to_upstream.py` (run once or as an hourly cron).
- Verification Guard: Verifies unit tests pass before attempting git operations.
- Feature Branch Sync: Automatically branches `canonica/auto-learned-extractors-<timestamp>`, commits, and pushes upstream with pull request links.

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
- `source`: File path or document identifier.
- `sheet`: Sheet name.
- `row`, `column`, `address`: Exact coordinate (e.g. `B145`).
- `cells`: Complete tuple of `CellLocation` records.
- Interoperable with `aip_utils.Provenance`.