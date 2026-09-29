"""Unit tests for ExtractorRegistry."""

from aip_canonica.extractors.registry import ExtractorRegistry, get_default_registry
from aip_canonica.models import DocumentType, Workbook


class DummyExtractor:
    def __init__(self, name: str, match_result: bool = True):
        self._name = name
        self._match = match_result

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.BANK_STATEMENT

    @property
    def name(self) -> str:
        return self._name

    def matches(self, workbook: Workbook) -> bool:
        return self._match

    def extract(self, workbook: Workbook, *, source_name: str = ""):
        """Placeholder to avoid accidental implementation."""
        raise NotImplementedError()


def test_default_registry_has_built_in_extractors():
    """Verify that the default registry includes expected built-in extractors."""
    reg = get_default_registry()
    extractors = reg.get_extractors()
    names = [e.name for e in extractors]

    assert "icici_bank_statement" in names
    assert "standard_bank_statement" in names
    assert "tabular_invoice" in names
    assert "tabular_ledger" in names


def test_registry_register_and_find():
    """Verify that registry can register and find extractors correctly."""
    reg = ExtractorRegistry()
    ext1 = DummyExtractor("dummy_false", match_result=False)
    ext2 = DummyExtractor("dummy_true", match_result=True)

    reg.register(ext1)
    reg.register(ext2)

    # Using a mock workbook as no real implementation is needed
    wb = Workbook()
    found = reg.find_extractor(wb)
    assert found is not None
    assert found.name == "dummy_true"


def test_registry_find_none():
    """Verify that registry returns None when no extractor matches."""
    reg = ExtractorRegistry()
    reg.register(DummyExtractor("dummy_false", match_result=False))
    assert reg.find_extractor(Workbook()) is None