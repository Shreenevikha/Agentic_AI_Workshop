from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, List
import re
from vendor_risk_analyzer.config import RISK_WEIGHTS, GOOGLE_API_KEY

class RiskSignalAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.0-pro",
            google_api_key=GOOGLE_API_KEY,
            temperature=0,
            convert_system_message_to_human=True
        )
        
    def validate_gstin(self, gstin: str) -> float:
        """Validate GSTIN format and return risk score."""
        if not gstin or len(gstin) != 15:
            return 1.0
            
        # Basic GSTIN validation
        if not gstin[0:2].isalpha() or not gstin[2:12].isdigit() or not gstin[12:].isalnum():
            return 1.0
            
        return 0.0

    def detect_irregular_billing(self, billing_history: Dict) -> float:
        """Detect irregular patterns in billing history."""
        if not billing_history:
            return 1.0
            
        # Analyze billing patterns
        prompt = f"""
        Analyze the following billing history for irregularities:
        {billing_history}
        
        Consider:
        1. Unusual payment amounts
        2. Irregular payment intervals
        3. Suspicious patterns
        
        Return a risk score between 0 and 1, where:
        0 = No irregularities
        1 = Severe irregularities
        """
        
        response = self.llm.invoke(prompt)
        try:
            return float(response.content.strip())
        except ValueError:
            return 0.5

    def analyze_risk_signals(self, vendor_data: Dict) -> Dict:
        """Analyze various risk signals in vendor data."""
        risk_signals = {
            "gstin_mismatch": self.validate_gstin(vendor_data.get("gstin", "")),
            "missing_documents": 1.0 if not vendor_data.get("documents") else 0.0,
            "irregular_billing": self.detect_irregular_billing(vendor_data.get("billing_history", {})),
            "legal_disputes": 1.0 if vendor_data.get("legal_history", {}).get("active_cases", 0) > 0 else 0.0
        }
        
        return risk_signals

    def calculate_weighted_risk(self, risk_signals: Dict) -> float:
        """Calculate weighted risk score based on signals."""
        weighted_score = sum(
            risk_signals[signal] * RISK_WEIGHTS[signal]
            for signal in risk_signals
        )
        return weighted_score / sum(RISK_WEIGHTS.values()) 