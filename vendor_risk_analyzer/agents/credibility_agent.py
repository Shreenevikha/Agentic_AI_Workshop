from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Tuple, List
from vendor_risk_analyzer.config import RISK_THRESHOLDS, GOOGLE_API_KEY

class CredibilityAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.0-pro",
            google_api_key=GOOGLE_API_KEY,
            temperature=0,
            convert_system_message_to_human=True
        )
        
    def generate_risk_assessment(self, vendor_data: Dict, risk_signals: Dict) -> Tuple[float, str]:
        """Generate comprehensive risk assessment and justification."""
        # Calculate base risk score
        risk_score = sum(risk_signals.values()) / len(risk_signals)
        
        # Generate risk level
        risk_level = self._determine_risk_level(risk_score)
        
        # Generate detailed justification
        justification = self._generate_justification(vendor_data, risk_signals, risk_level)
        
        return risk_score, justification
        
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score."""
        if risk_score <= RISK_THRESHOLDS["low"]:
            return "LOW"
        elif risk_score <= RISK_THRESHOLDS["medium"]:
            return "MEDIUM"
        else:
            return "HIGH"
            
    def _generate_justification(self, vendor_data: Dict, risk_signals: Dict, risk_level: str) -> str:
        """Generate detailed justification for the risk assessment."""
        # Prepare context for the LLM
        context = {
            "vendor_name": vendor_data.get("vendor_name", "Unknown"),
            "risk_level": risk_level,
            "risk_signals": risk_signals,
            "vendor_data": vendor_data
        }
        
        # Generate detailed analysis using LLM
        prompt = f"""
        Analyze the following vendor risk assessment and provide a detailed justification:
        
        Vendor: {context['vendor_name']}
        Risk Level: {context['risk_level']}
        
        Risk Signals:
        - GSTIN Mismatch: {context['risk_signals']['gstin_mismatch']}
        - Missing Documents: {context['risk_signals']['missing_documents']}
        - Irregular Billing: {context['risk_signals']['irregular_billing']}
        - Legal Disputes: {context['risk_signals']['legal_disputes']}
        
        Please provide a detailed analysis of the risk factors and recommendations for risk mitigation.
        """
        
        response = self.llm.invoke(prompt)
        return response.content
        
    def generate_recommendations(self, risk_assessment: Tuple[float, str]) -> List[str]:
        """Generate specific recommendations based on risk assessment."""
        risk_score, justification = risk_assessment
        
        prompt = f"""
        Based on the following risk assessment, provide specific, actionable recommendations:
        
        Risk Score: {risk_score}
        Justification: {justification}
        
        Please provide 3-5 specific recommendations for risk mitigation or vendor management.
        """
        
        response = self.llm.invoke(prompt)
        return response.content.split('\n') 