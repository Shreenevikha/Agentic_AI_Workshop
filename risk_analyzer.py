from typing import Dict, List
import logging
import re
from datetime import datetime

class RiskAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.risk_patterns = {
            'financial': [
                r'(?i)overdue|outstanding|pending payment|late payment',
                r'(?i)bankruptcy|insolvency|liquidation',
                r'(?i)financial distress|financial difficulty',
                r'(?i)default|breach of contract'
            ],
            'compliance': [
                r'(?i)expired.*gstin|invalid.*gstin',
                r'(?i)expired.*pan|invalid.*pan',
                r'(?i)non-compliant|violation|breach',
                r'(?i)regulatory.*issue|compliance.*issue'
            ],
            'legal': [
                r'(?i)lawsuit|litigation|legal action',
                r'(?i)court case|legal dispute',
                r'(?i)breach of contract|contract violation',
                r'(?i)legal notice|cease and desist'
            ],
            'operational': [
                r'(?i)delayed delivery|late delivery',
                r'(?i)quality issue|defect|faulty',
                r'(?i)service disruption|outage',
                r'(?i)capacity issue|resource constraint'
            ]
        }

    def analyze(self, processed_docs: Dict) -> Dict:
        """
        Analyze processed documents for risk signals
        
        Args:
            processed_docs: Dictionary containing processed document data
            
        Returns:
            Dictionary containing risk analysis results
        """
        try:
            risk_analysis = {
                'risk_factors': [],
                'risk_categories': {
                    'financial': [],
                    'compliance': [],
                    'legal': [],
                    'operational': []
                },
                'risk_level': 'low',
                'timestamp': datetime.now().isoformat()
            }

            # Analyze each document
            for doc in processed_docs.get('processed_documents', []):
                text = doc.get('extracted_text', '')
                if not text:
                    continue

                # Check each risk category
                for category, patterns in self.risk_patterns.items():
                    for pattern in patterns:
                        matches = re.finditer(pattern, text)
                        for match in matches:
                            risk_factor = {
                                'category': category,
                                'pattern': pattern,
                                'context': self._get_context(text, match.start(), match.end()),
                                'severity': self._get_severity(category, pattern)
                            }
                            risk_analysis['risk_factors'].append(risk_factor)
                            risk_analysis['risk_categories'][category].append(risk_factor)

            # Calculate overall risk level
            risk_analysis['risk_level'] = self._calculate_risk_level(risk_analysis['risk_factors'])

            return risk_analysis

        except Exception as e:
            self.logger.error(f"Error analyzing documents: {str(e)}")
            raise

    def _get_context(self, text: str, start: int, end: int, context_size: int = 100) -> str:
        """Extract context around matched pattern"""
        start = max(0, start - context_size)
        end = min(len(text), end + context_size)
        return text[start:end].strip()

    def _get_severity(self, category: str, pattern: str) -> str:
        """Determine severity of risk factor"""
        # Define severity based on category and pattern
        severity_map = {
            'financial': {
                r'bankruptcy|insolvency': 'high',
                r'overdue|outstanding': 'medium',
                r'default': 'high'
            },
            'compliance': {
                r'expired.*gstin|invalid.*gstin': 'high',
                r'non-compliant': 'medium',
                r'violation': 'high'
            },
            'legal': {
                r'lawsuit|litigation': 'high',
                r'legal dispute': 'medium',
                r'breach of contract': 'high'
            },
            'operational': {
                r'delayed delivery': 'medium',
                r'quality issue': 'high',
                r'service disruption': 'medium'
            }
        }

        # Check category-specific patterns
        if category in severity_map:
            for pattern_key, severity in severity_map[category].items():
                if re.search(pattern_key, pattern, re.IGNORECASE):
                    return severity

        # Default severity
        return 'medium'

    def _calculate_risk_level(self, risk_factors: List[Dict]) -> str:
        """Calculate overall risk level based on risk factors"""
        if not risk_factors:
            return 'low'

        # Count risk factors by severity
        severity_counts = {
            'high': 0,
            'medium': 0,
            'low': 0
        }

        for factor in risk_factors:
            severity = factor.get('severity', 'medium')
            severity_counts[severity] += 1

        # Determine risk level based on severity counts
        if severity_counts['high'] > 0:
            return 'high'
        elif severity_counts['medium'] > 1:
            return 'medium'
        else:
            return 'low' 