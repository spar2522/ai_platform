"""Unit tests for StrategyLearner using mock aip-provider AI."""

from unittest.mock import AsyncMock
import pytest

from aip_canonica.learning.learner import StrategyLearner
from aip_canonica.learning.strategy import LearnedStrategy
from aip_canonica.models import DocumentType, Workbook
from aip_provider.models import AIResponse


@pytest.mark.asyncio
async def test_strategy_learner_parses_ai_response():
    """Verify that a valid AI response with JSON format is correctly parsed."""
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
    assert "A/C No:" == strategy.metadata_fields["account_number"]
    assert mock_ai.generate.called


@pytest.mark.asyncio
async def test_strategy_learner_handles_malformed_ai_response():
    """Verify that a malformed AI response falls back to default strategy."""
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