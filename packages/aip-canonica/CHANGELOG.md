# Changelog

All notable changes to this project will be documented in this file.

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
- Replaced old workbook-only `understand()` with canonical document returning function.
- Refactored legacy `interpreters` architecture to composition-based `extractors` protocol and registry.

## [0.1.0]

### Added
- Initial project prototype with Excel parser and Workbook models.