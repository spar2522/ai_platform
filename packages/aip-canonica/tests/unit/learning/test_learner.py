"""Unit tests for StrategyLearner using mock aip-provider AI."""

from unittest.mock import AsyncMock
import pytest

from aip_canonica.learning.learner import StrategyLearner
from aip_canonica.learning.strategy import LearnedStrategy
from aip_canonica.models import DocumentType, Workbook
from aip_provider.models import AIResponse


@pytest.mark.asyncio
async def test_strategy_learner_parses_ai_response():
    mock_ai = AsyncMock()
    mock_ai.generate.return_value = AIResponse(
        text="""```json
{
    "name": "custom_bank_statement",
    "document_type": "bank_statement",
    "anchor_keywords": ["account number", "statement"],
    "table_header_keywords": ["date", "particulars", "dr", "cr", "bal"],
    "column_mapping": {
        "date": "Txn Date",
        "narration": "Details",
        "debit": "Dr",
        "credit": "Cr"
    },
    "metadata_fields": {
        "account_number": "A/C No:"
    },
    "notes": "Custom local cooperative bank statement"
}
```""",
        model="mock-model",
    )

    learner = StrategyLearner(ai=mock_ai)
    strategy = await learner.learn_from_workbook(Workbook(), name="custom_bank_statement")

    assert isinstance(strategy, LearnedStrategy)
    assert strategy.name == "custom_bank_statement"
    assert strategy.document_type == DocumentType.BANK_STATEMENT
    assert "Txn Date" == strategy.column_mapping["date"]
    assert mock_ai.generate.called


@pytest.mark.asyncio
async def test_strategy_learner_handles_malformed_json():
    mock_ai = AsyncMock()
    mock_ai.generate.return_value = AIResponse(
        text="I could not determine the layout format.",
        model="mock-model",
    )

    learner = StrategyLearner(ai=mock_ai)
    strategy = await learner.learn_from_workbook(Workbook(), name="fallback_test")

    assert isinstance(strategy, LearnedStrategy)
    assert strategy.name == "fallback_test"
    assert strategy.document_type == DocumentType.BANK_STATEMENT


@pytest.mark.asyncio
async def test_strategy_learner_evolution_with_existing_extractor():
    from aip_canonica.models import Cell, Row, Sheet

    mock_ai = AsyncMock()
    mock_ai.generate.return_value = AIResponse(
        text="""```json
{
    "name": "axis_bank_statement",
    "document_type": "bank_statement",
    "layout_type": "multiline_block",
    "strategy_action": "evolve_existing",
    "related_extractor_name": "axis_bank_statement",
    "anchor_keywords": ["statement of axis account", "utib0005157"],
    "table_header_keywords": ["tran date", "particulars", "debit", "credit", "balance"],
    "column_mapping": {},
    "metadata_fields": {
        "account_number": "Statement of Axis Account No :",
        "customer_id": "Customer ID :"
    },
    "block_delimiters": {
        "record_start_regex": "^(\\\\d{2}-\\\\d{2}-\\\\d{4})",
        "amount_balance_pattern": "(\\\\d+\\\\.\\\\d{2})"
    },
    "notes": "Evolving AxisBankStatementExtractor to support multiline PDF layout alongside tabular"
}
```""",
        model="mock-model",
    )

    wb = Workbook(
        sheets=[
            Sheet(
                name="Page_1",
                rows=[
                    Row(index=0, cells=[Cell(value="Statement of Axis Account No : 5145922811", location="A1")]),
                    Row(index=1, cells=[Cell(value="IFSC Code : UTIB0005157", location="A2")]),
                ],
            )
        ]
    )

    learner = StrategyLearner(ai=mock_ai)
    strategy = await learner.learn_from_workbook(wb)

    assert strategy.name == "axis_bank_statement"
    assert strategy.evolution_mode == "evolve_existing"
    assert strategy.layout_type == "multiline_block"
    assert strategy.related_extractor_name == "axis_bank_statement"
    assert strategy.block_delimiters["record_start_regex"] == r"^(\d{2}-\d{2}-\d{4})"

    # Verify existing extractor source code was injected into the prompt
    assert mock_ai.generate.called
    call_kwargs = mock_ai.generate.call_args.kwargs
    prompt = call_kwargs["prompt"]
    assert "EXISTING REGISTERED EXTRACTOR FOR THIS INSTITUTION:" in prompt
    assert "AxisBankStatementExtractor" in prompt
    assert "EVOLVE this existing extractor" in prompt

    code = learner.generate_extractor_code(strategy, existing_code="class AxisBankStatementExtractor: pass")
    assert "EVOLVED UNIFIED EXTRACTOR" in code
    assert "multiline_block" in code

