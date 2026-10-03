"""Learning package for offline AI-assisted document strategy discovery."""

from aip_canonica.learning.learner import StrategyLearner
from aip_canonica.learning.strategy import LearnedStrategy, LearningReport

__all__ = [
    "LearnedStrategy",
    "LearningReport",
    "StrategyLearner",
]
