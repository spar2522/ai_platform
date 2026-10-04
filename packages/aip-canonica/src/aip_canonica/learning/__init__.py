"""Learning package for offline AI-assisted document strategy discovery.

This module provides tools for training and managing strategies using offline AI learning. It includes the StrategyLearner class for training strategies, LearnedStrategy for representing trained strategies, and LearningReport for storing learning outcomes.
"""

from aip_canonica.learning.learner import StrategyLearner
from aip_canonica.learning.strategy import LearnedStrategy, LearningReport

__all__ = [
    "LearnedStrategy",
    "LearningReport",
    "StrategyLearner",
]