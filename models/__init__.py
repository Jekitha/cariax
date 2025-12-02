"""
Models package initialization
"""

from .ml_models import (
    SkillPredictionModel,
    PersonalityPredictionModel,
    CareerRecommendationModel,
    SalaryPredictionModel,
    JobMarketTrendAnalyzer,
    ScamContentDetector
)

__all__ = [
    'SkillPredictionModel',
    'PersonalityPredictionModel',
    'CareerRecommendationModel',
    'SalaryPredictionModel',
    'JobMarketTrendAnalyzer',
    'ScamContentDetector'
]
