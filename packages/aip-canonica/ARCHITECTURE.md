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
Defines canonical financial models and graph traversal capabilities.
- `BankStatement`, `Invoice`, `Ledger`, `Tax`, `Party`, `InvoiceLine`: Core domain entities with rich metadata.
- `Graph`: Central abstraction for traversing relationships between entities.
- `.as_graph()`: Method on canonical documents to populate nodes and directed edges.

### C. Extractor Layer (`aip_canonica.extractors`)
Responsible for identifying and extracting meaningful data from raw documents.
- `Extractor`: Base class for all document parsers.
- `AxisBankStatementExtractor`: Handles multi-layout bank statements from Axis Bank.
- `Registry`: Central registry for all extractors, enabling dynamic plugin loading.

### D. AI Learning Layer (`aip_canonica.ai`)
Leverages AI to adapt to new document layouts and formats.
- `GeminiAdapter`: Interface to Gemini 3.8 Flash for layout analysis.
- `MultiLayoutEvolver`: Evolves existing extractors to support new document variants.
- `LearnedStrategy`: Encapsulates AI-derived parsing rules and mappings.

### E. Promotion Engine (`aip_canonica.promotion`)
Automates the deployment of new extractors into production.
- `Locker`: Ensures thread-safe and process-safe installation using `threading.RLock` and `fcntl.flock`.
- `CodeAnalyzer`: Identifies primary `Extractor` classes in synthesized code.
- `WiringEngine`: Deploys new extractors into appropriate directories and updates `registry.py`.

### F. Upstream Synchronization (`aip_canonica.publishing`)
Maintains synchronization with upstream repositories.
- `BatchRunner`: Executes synchronization tasks independently of request processing.
- `VerificationService`: Ensures unit tests pass before initiating git operations.
- `BranchManager`: Creates feature branches for new extractors with timestamped names.

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