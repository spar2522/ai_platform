"""Unit tests for ExtractorRegistry."""

from aip_canonica.extractors.registry import ExtractorRegistry, get_default_registry
from aip_canonica.models import DocumentType, Workbook


class DummyExtractor:
    """A dummy extractor for testing purposes."""

    def __init__(self, name: str, match_result: bool = True):
        """Initialize the extractor with a name and match result."""
        self._name = name
        self._match = match_result

    @property
    def document_type(self) -> DocumentType:
        """Return the document type supported by this extractor."""
        return DocumentType.BANK_STATEMENT

    @property
    def name(self) -> str:
        """Return the name of this extractor."""
        return self._name

    def matches(self, workbook: Workbook) -> bool:
        """Determine if this extractor matches the given workbook."""
        return self._match

    def extract(self, workbook: Workbook, *, source_name: str = ""):
        """Extract data from the workbook (not implemented in dummy)."""
        raise NotImplementedError()


def test_default_registry_contains_expected_extractors():
    """Verify that the default registry includes built-in extractors."""
    reg = get_default_registry()
    extractors = reg.get_extractors()
    names = [e.name for e in extractors]

    expected_names = {
        "icici_bank_statement",
        "standard_bank_statement",
        "tabular_invoice",
        "tabular_ledger",
    }
    assert expected_names.issubset(names), "Missing expected extractors in default registry"


def test_registry_can_register_and_find_extractor():
    """Verify that the registry can register and find extractors."""
    reg = ExtractorRegistry()
    ext1 = DummyExtractor("dummy_false", match_result=False)
    ext2 = DummyExtractor("dummy_true", match_result=True)

    reg.register(ext1)
    reg.register(ext2)

    workbook = Workbook()
    found = reg.find_extractor(workbook)
    assert found is not None, "Registry failed to find a matching extractor"
    assert found.name == "dummy_true", "Registry returned incorrect extractor"


def test_registry_returns_none_when_no_match():
    """Verify that the registry returns None when no extractors match."""
    reg = ExtractorRegistry()
    reg.register(DummyExtractor("dummy_false", match_result=False))
    assert reg.find_extractor(Workbook()) is None, "Registry should return None when no extractor matches"