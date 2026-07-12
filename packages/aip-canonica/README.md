# Canonica

> Turn business documents into business objects.

Canonica is an extensible document understanding framework that converts
business documents into strongly typed canonical models.

Instead of writing custom parsers, regular expressions, or prompts for every
document format, simply call:

```python
from aip_canonica import understand

document = understand("statement.xlsx")
```

Canonica automatically:

- Detects the document family.
- Selects the appropriate interpreter.
- Produces a canonical business model.
- Learns new document formats.
- Executes deterministically for known document families.

---

## Philosophy

### Canonical models over extracted text

Applications should receive business objects rather than OCR text,
tables or JSON blobs.

### AI teaches. Deterministic code runs.

AI is used only to teach Canonica new document families.

Once an interpreter has been learned and validated,
future documents execute deterministically.

### Intelligence agnostic

Canonica works with any provider supported by `aip-provider`.

- Gemini
- OpenAI
- Claude
- Ollama
- vLLM
- Local models
- Custom enterprise providers

### Privacy first

Documents are never processed outside your infrastructure unless
explicitly allowed.

---

## Example

```python
from aip_canonica import understand

statement = understand("statement.xlsx")

print(statement.transactions)
```

---

## Vision

Business software should not care whether a document originated from

- HDFC
- ICICI
- SBI
- SAP
- Oracle
- Tally
- Marg
- QuickBooks

Applications should simply receive canonical business objects.

---

## Status

🚧 Under active development.