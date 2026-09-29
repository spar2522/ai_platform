To improve the **readability**, **maintainability**, and **documentation** of the test suite, the following changes have been made:

---

### ✅ **Improvements Applied**

1. **Moved `PdfParser` import to the top** of the module to ensure all imports are centralized and consistent with Python best practices.

2. **Added docstrings to each test function** to clearly describe the purpose and expected outcome of the test, improving documentation and making the tests more understandable for future maintainers.

3. **Improved test file names and paths** for clarity and correctness, ensuring that the test cases are descriptive and meaningful.

---

### 📄 **Updated Test File**

```python
from pathlib import Path
import pytest

from aip_canonica.parsers import (
    CsvParser,
    ExcelParser,
    ParserFactory,
    PdfParser,
)


def test_excel_parser_selected():
    """Verify that ExcelParser is selected for .xlsx files."""
    parser = ParserFactory.create(Path("statement.xlsx"))
    assert isinstance(parser, ExcelParser)


def test_csv_parser_selected():
    """Verify that CsvParser is selected for .csv files."""
    parser = ParserFactory.create(Path("statement.csv"))
    assert isinstance(parser, CsvParser)


def test_pdf_parser_selected():
    """Verify that PdfParser is selected for .pdf files."""
    parser = ParserFactory.create(Path("statement.pdf"))
    assert isinstance(parser, PdfParser)


def test_unsupported_parser_selected():
    """Verify that a ValueError is raised for unsupported file types."""
    with pytest.raises(ValueError, match="Unsupported document type"):
        ParserFactory.create(Path("statement.unknown"))
```

---

### 📌 **Summary of Changes**

| Aspect             | Before                          | After                           |
|--------------------|---------------------------------|---------------------------------|
| **Import Style**   | `PdfParser` imported inside test | `PdfParser` imported at top     |
| **Documentation**  | No docstrings                   | Each test has a descriptive docstring |
| **Test Structure** | Separate tests for each file type | Same structure but with improved clarity and documentation |

---

### 🧪 **Test Coverage**

- ✅ **Excel file** (`.xlsx`) → `ExcelParser` is selected
- ✅ **CSV file** (`.csv`) → `CsvParser` is selected
- ✅ **PDF file** (`.pdf`) → `PdfParser` is selected
- ✅ **Unknown file type** → Raises `ValueError` with the expected message

---

This improved version of the test file is now more maintainable, readable, and well-documented, while preserving the original functionality and behavior of the tests.