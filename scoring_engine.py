from typing import Dict, List
import logging
from datetime import datetime

class ScoringEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.risk_weights = {
            'financial': 0.4,
            'compliance': 0.3,
            'legal': 0.2,
            'operational': 0.1
        }
        self.severity_scores = {
            'low': 1,
            'medium': 3,
            'high': 5
        }

    def calculate_score(self, analysis_results: Dict) -> Dict:
        """
        Calculates a comprehensive credibility score based on risk analysis.

        Args:
            analysis_results: Dictionary containing risk analysis results from RiskAnalyzer.

        Returns:
            Dictionary with the overall score, risk level, and component scores.
        """
        total_weighted_score = 0
        total_weight = 0
        component_scores = {}

        risk_factors = analysis_results.get('risk_analysis', {}).get('risk_factors', [])
        
        # Initialize scores for all categories
        for category in self.risk_weights.keys():
            component_scores[category] = 0

        for factor in risk_factors:
            category = factor.get('category')
            severity = factor.get('severity', 'low').lower()
            
            if category in self.risk_weights and severity in self.severity_scores:
                severity_score = self.severity_scores[severity]
                component_scores[category] += severity_score # Sum severity scores for each category

        # Calculate weighted average for each component and overall score
        for category, weight in self.risk_weights.items():
            score_for_category = component_scores.get(category, 0)
            # Normalize score_for_category, assuming max severity score for a single factor is 5
            # If multiple factors can be in one category, this normalization needs adjustment
            # For simplicity, let's assume maximum possible severity score for a category is proportional to num factors or a fixed max.
            # For now, let's just sum and then normalize based on a hypothetical max per category if needed

            # Simple normalization for demonstration: assume max possible score for a category is 10 (e.g., 2 high risks)
            normalized_score = min(score_for_category / 10, 1.0) # Cap at 1.0
            total_weighted_score += normalized_score * weight
            total_weight += weight
        
        overall_score = 0
        if total_weight > 0:
            overall_score = (1 - (total_weighted_score / total_weight)) * 100 # Invert for credibility score (higher is better)
        else:
            overall_score = 100 # No risks, perfect score

        overall_risk_level = self._determine_overall_risk_level(overall_score)

        return {
            "score": round(overall_score, 2),
            "risk_level": overall_risk_level,
            "components": component_scores
        }

    def _determine_overall_risk_level(self, score: float) -> str:
        """
        Determines the overall risk level based on the calculated score.
        """
        if score < 40:
            return "high"
        elif score < 70:
            return "medium"
        else:
            return "low"

    def _calculate_component_score(self, category: str, risks: list) -> float:
        """Calculate score for a specific risk category"""
        if not risks:
            return 0.0

        # Base score on number of risks and their severity
        base_score = min(len(risks) * 0.2, 1.0)  # Each risk adds 0.2, max 1.0

        # Adjust score based on category-specific factors
        if category == 'financial':
            # Financial risks are weighted more heavily
            return base_score * 1.2
        elif category == 'compliance':
            # Compliance risks have standard weight
            return base_score
        elif category == 'legal':
            # Legal risks are weighted more heavily
            return base_score * 1.2
        else:  # operational
            # Operational risks have standard weight
            return base_score

    def _get_risk_level(self, score: int) -> str:
        """Convert numerical score to risk level"""
        if score < 30:
            return "low"
        elif score < 70:
            return "medium"
        else:
            return "high" 