"""Canonica: Turn business documents into business objects."""

from .api import parse_document, understand, validate
from .config import configure
from .exceptions import (
    CanonicaError,
    CanonicaException,
    ExtractionError,
    ParseError,
    UnknownDocumentError,
    UnsupportedDocumentError,
    ValidationError,
)
from .extractors.base import Extractor
from .extractors.registry import ExtractorRegistry, get_default_registry
from .models import (
    Account,
    BankStatement,
    CanonicalDocument,
    CanonicalGraph,
    CanonicalNode,
    Cell,
    CellLocation,
    DatePeriod,
    Discount,
    DocumentType,
    EntryDirection,
    InterestCertificate,
    Invoice,
    InvoiceLine,
    Ledger,
    LedgerEntry,
    Money,
    Party,
    Provenance,
    Relationship,
    Row,
    Sheet,
    Tax,
    TDSCertificate,
    TDSEntry,
    Transaction,
    TransactionDirection,
    Workbook,
)
from .learning import LearnedStrategy, LearningReport, StrategyLearner
from .validation.result import Finding, Severity, ValidationResult
from .validation.validator import FinancialValidator

# Backwards compatibility and alternative naming aliases
BankTransaction = Transaction
InvoiceLineItem = InvoiceLine
InvoiceParty = Party
GeneralLedger = Ledger
JournalEntry = LedgerEntry
JournalLine = LedgerEntry
RelationshipGraph = CanonicalGraph
GraphNode = CanonicalNode
GraphEdge = Relationship

__version__ = "0.2.0"

__all__ = [
    # Core API
    "understand",
    "validate",
    "parse_document",
    "configure",
    # Models
    "CanonicalDocument",
    "BankStatement",
    "BankTransaction",
    "Transaction",
    "Invoice",
    "InvoiceLine",
    "InvoiceLineItem",
    "InvoiceParty",
    "Ledger",
    "GeneralLedger",
    "LedgerEntry",
    "JournalEntry",
    "JournalLine",
    "EntryDirection",
    "Party",
    "Account",
    "Provenance",
    "DocumentType",
    "RelationshipGraph",
    "CanonicalGraph",
    "GraphNode",
    "CanonicalNode",
    "GraphEdge",
    "Relationship",
    "Workbook",
    "Sheet",
    "Row",
    "Cell",
    "CellLocation",
    "Tax",
    "Discount",
    "TDSCertificate",
    "TDSEntry",
    "InterestCertificate",
    "DatePeriod",
    "Money",
    "TransactionDirection",
    # Extractors
    "Extractor",
    "ExtractorRegistry",
    "get_default_registry",
    # Learning
    "StrategyLearner",
    "LearnedStrategy",
    "LearningReport",
    # Validation
    "FinancialValidator",
    "ValidationResult",
    "Finding",
    "Severity",
    # Exceptions
    "CanonicaError",
    "CanonicaException",
    "ParseError",
    "UnsupportedDocumentError",
    "UnknownDocumentError",
    "ExtractionError",
    "ValidationError",
]