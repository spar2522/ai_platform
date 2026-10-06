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
  - `BankStatement`, `Ledger`, `Invoice`, `InterestCertificate`, `TDSCertificate`
  - Entities like `Party`, `Tax`, `InvoiceLine`

### C. Extractor Layer (`aip_canonica.extractors`)
- **Purpose**: Convert raw documents into canonical models via layout-specific rules.
- **Key Components**:
  - `ExtractorRegistry`: Centralized registry for all layout extractors.
  - `LayoutExtractor`: Base class for document-specific extractors.
  - **Built-in Extractors**:
    - `AxisBankStatementExtractor`: Handles multi-layout bank statements.
    - `StandardInvoiceExtractor`: Processes standard invoice formats.
    - `TaxCertificateExtractor`: Parses tax-related documents.

### D. AI Learning Layer (`aip_canonica.ai`)
- **Purpose**: Automate extractor evolution through AI-assisted analysis.
- **Key Features**:
  - `AIAnalyzer`: Queries AI models (e.g., Gemini 3.8 Flash) to identify document patterns.
  - **Multi-Layout Evolution**: Automatically merges new layouts into existing extractors.
  - Output: `LearnedStrategy` and synthetic Python code in `.canonica/generated/`

### E. Autonomous Promotion Engine (`aip_canonica.promotion`)
- **Concurrency Safety**: Uses `threading.RLock()` and `fcntl.flock()` for safe deployment.
- **Code Integration**:
  - AST-based class identification in generated code.
  - Automated code placement in `aip_canonica/extractors/<category>/`.
  - Linting with `ruff` before deployment.

### F. Upstream Synchronization (`aip_canonica.publishing`)
- **Batch Processing**: Independent execution via `scripts/sync_extractors_to_upstream.py`.
- **Quality Assurance**:
  - Unit test verification before git operations.
  - Git branch creation: `canonica/auto-learned-extractors-<timestamp>`
  - Pull request automation with upstream repository.

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

This tracking enables:
- **Auditability**: Traceable document origins.
- **Validation**: Cross-checking data against source coordinates.
- **Reconciliation**: Resolving discrepancies through source-level analysis.