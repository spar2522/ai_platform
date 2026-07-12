# Architecture

## Goal

Convert any business document into a canonical business model.

```
Document
        │
        ▼
Document Parser (internal)
        │
        ▼
Interpreter Registry
        │
        ▼
Interpreter
        │
        ▼
Canonical Business Model
```

Learning is a separate pipeline.

```
Unknown Document
        │
        ▼
Learning Engine
        │
        ▼
Interpreter DSL
        │
        ▼
Compiler
        │
        ▼
Regression Tests
        │
        ▼
Interpreter Registry
```

Runtime never depends on AI.

AI is only used to create new interpreters.

---

## Public API

```python
from aip_canonica import understand

document = understand("statement.xlsx")
```

Everything else is considered an implementation detail.

---

## Principles

- Public API should remain extremely small.
- Runtime execution must be deterministic.
- Unknown documents should trigger learning, not failure (when enabled).
- Every interpreter must validate its own output.
- Canonical business models are the primary abstraction.