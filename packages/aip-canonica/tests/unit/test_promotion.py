"""Unit tests for the autonomous extractor promotion engine."""

from pathlib import Path
import threading

from aip_canonica.promotion import (
    find_extractor_class_name,
    promote_extractor,
    promotion_lock,
    register_extractor_in_registry,
)


SAMPLE_EXTRACTOR_CODE = '''"""Sample generated extractor."""

from aip_canonica.models import DocumentType, Workbook
from aip_canonica.models.bank_statement import BankStatement


class MockTestExtractor:
    """Mock extractor for testing."""

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.BANK_STATEMENT

    @property
    def name(self) -> str:
        return "mock_test"

    @property
    def is_generic(self) -> bool:
        return False

    def matches(self, workbook: Workbook) -> bool:
        return True

    def extract(self, workbook: Workbook, *, source_name: str = "") -> BankStatement:
        return BankStatement(id="mock", opening_balance=None, closing_balance=None, transactions=[])
'''

SAMPLE_REGISTRY_CODE = '''"""Registry for discovering extractors."""

from aip_canonica.extractors.bank.standard import StandardBankStatementExtractor
from aip_canonica.extractors.base import Extractor


class ExtractorRegistry:
    def __init__(self, extractors=None):
        self._extractors = list(extractors or [])

    def register(self, extractor):
        self._extractors.append(extractor)


_DEFAULT_REGISTRY = None


def get_default_registry() -> ExtractorRegistry:
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = ExtractorRegistry(
            [
                StandardBankStatementExtractor(),
            ]
        )
    return _DEFAULT_REGISTRY
'''


def test_find_extractor_class_name():
    """Verify that find_extractor_class_name correctly identifies the class name from code."""
    name = find_extractor_class_name(SAMPLE_EXTRACTOR_CODE)
    assert name == "MockTestExtractor"


def test_register_extractor_in_registry(tmp_path: Path):
    """Test registration of an extractor in a registry file, including idempotency."""
    registry_file = tmp_path / "registry.py"
    registry_file.write_text(SAMPLE_REGISTRY_CODE, encoding="utf-8")

    # First registration should succeed and modify the file
    updated = register_extractor_in_registry(
        registry_file=registry_file,
        category="bank",
        module_slug="mock_test",
        class_name="MockTestExtractor",
    )
    assert updated is True

    content = registry_file.read_text(encoding="utf-8")
    assert "from aip_canonica.extractors.bank.mock_test import MockTestExtractor" in content
    assert "MockTestExtractor()," in content

    # Second registration should be idempotent and not modify the file
    second_updated = register_extractor_in_registry(
        registry_file=registry_file,
        category="bank",
        module_slug="mock_test",
        class_name="MockTestExtractor",
    )
    assert second_updated is False


def test_promote_extractor_end_to_end(tmp_path: Path):
    """Test end-to-end promotion of an extractor, including registry update."""
    source_file = tmp_path / "mock_test_strategy_extractor.py"
    source_file.write_text(SAMPLE_EXTRACTOR_CODE, encoding="utf-8")

    extractors_root = tmp_path / "extractors"
    extractors_root.mkdir(parents=True)
    registry_file = extractors_root / "registry.py"
    registry_file.write_text(SAMPLE_REGISTRY_CODE, encoding="utf-8")

    promoted_file = promote_extractor(
        source_path=source_file,
        category="bank",
        extractors_root=extractors_root,
        auto_register=True,
        format_code=False,
    )

    assert promoted_file.exists()
    assert promoted_file.name == "mock_test.py"
    registry_content = registry_file.read_text(encoding="utf-8")
    assert "MockTestExtractor" in registry_content


def test_promotion_lock_concurrency(tmp_path: Path):
    """Verify that the promotion lock properly serializes concurrent operations."""
    lock_file = tmp_path / ".promotion.lock"
    counter = 0

    def worker():
        nonlocal counter
        with promotion_lock(lock_file):
            val = counter
            # Simulated work
            counter = val + 1

    # Create and start threads
    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Ensure all threads completed successfully
    assert counter == 10