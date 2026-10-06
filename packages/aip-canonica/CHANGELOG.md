# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0] - 2026-10-04

### Added
- **Multi-Layout Extractor Architecture**: Introduced `AxisBankStatementExtractor` supporting both 1-row tabular spreadsheets (XLS) and wrapped multiline block layouts (PDF) with automatic layout detection.
- **Autonomous Promotion Engine**: Added `aip_canonica.promotion` with OS-level `fcntl.flock` and `threading.RLock` concurrency safety, automated class detection, registration in `registry.py`, and code formatting.
- **LLM Multi-Layout Evolutionary Synthesis**: Enhanced `StrategyLearner` to support evolutionary synthesis via Gemini 3.8 Flash, extending existing single-layout extractors into unified multi-layout classes.
- **Decoupled Upstream Git Synchronization**: Added `aip_canonica.publishing` and `scripts/sync_extractors_to_upstream.py` background job to safely test, branch, and push promoted extractors to GitHub.
- **PDF Vector Parsing & Multi-Page Support**: Added `PdfParser` with multi-page table text extraction and fallback recovery.
- **Legacy XLS Support**: Added `xlrd` support in `ExcelParser` for parsing legacy `.xls` binary workbooks.
- **Audit & Token Tracking**: Added token usage logging (`log_token_usage`) and AI connectivity notices.
- **Verification & Benchmarking Tools**: Added `scripts/verify_canonica.py` (`--learn`, `--promote`, `--debug`), `scripts/promote_extractor.py`, and `scripts/compare_extractors.py`.

## [0.2.0] - 2026-09-26

### Added
- **Canonical Financial Models**: Added generic, typed representations for `BankStatement`, `Ledger`, `Invoice` (single generic model for sales/purchases), `InterestCertificate`, and `TDSCertificate`.
- **Graph Compatibility**: Added `CanonicalGraph` and `Relationship` models supporting directed graph construction, outgoing traversal, incoming relationship discovery, and JSON serialization.
- **First-Class Provenance**: Added `Provenance` tracking exact source cells (`CellLocation`), rows, and lines, with direct bridge to `aip_utils.Provenance`.
- **Deterministic Extractors**: Added `ICICIBankStatementExtractor` (supporting 1500+ transactions and metadata offsets), `StandardBankStatementExtractor`, `TabularInvoiceExtractor`, and `TabularLedgerExtractor`.
- **Deterministic Validation**: Added `BankStatementValidator`, `InvoiceValidator`, and `LedgerValidator` for mathematical reconciliation producing structured `ValidationResult`.
- **CSV Parser**: Implemented full `CsvParser` with dialect sniffing, handling varied line breaks, quotes, and empty rows.
- **AI Learning Seam**: Added isolated offline `StrategyLearner` utilizing `aip_provider.AI` for layout discovery, with zero runtime AI overhead.
- **Public API**: Streamlined top-level API to `understand()`, `validate()`, and `parse_document()`.

### Changed
- Replaced the old workbook-only `understand()` function with a new canonical document returning function.
- Refactored legacy `interpreters` architecture to composition-based `extractors` protocol and registry.

## [0.1.0]

### Added
- Initial project prototype with Excel parser and Workbook models.