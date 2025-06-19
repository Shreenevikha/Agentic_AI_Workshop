"""
Credibility Scoring Agent
Aggregates insights and generates a vendor risk score and justification.
"""

from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

class CredibilityScoringAgent:
    def __init__(self, llm=None):
        self.llm = llm
        self.use_gemini = config.is_gemini_available()
        
        if self.use_gemini and llm is None:
            try:
                gemini_config = config.get_gemini_config()
                self.llm = ChatGoogleGenerativeAI(
                    google_api_key=gemini_config["api_key"],
                    model=gemini_config["model"],
                    temperature=gemini_config["temperature"]
                )
                self.setup_agent()
            except Exception as e:
                print(f"⚠️  Gemini initialization failed: {e}")
                self.use_gemini = False
        
        if not self.use_gemini:
            print("🔄 Using fallback credibility scoring (rule-based analysis)")
        
    def generate_risk_score(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate agent outputs and generate a risk score and justification."""
        try:
            # Extract data from agent outputs
            extracted_fields = agent_outputs.get("extracted_fields", {})
            risk_signals = agent_outputs.get("risk_signals", [])
            external_intelligence = agent_outputs.get("external_intelligence", {})
            
            if self.use_gemini and self.llm:
                # Use LLM to generate comprehensive risk assessment
                scoring_prompt = PromptTemplate(
                    input_variables=["extracted_fields", "risk_signals", "external_intelligence"],
                    template="""
                    Analyze the following vendor risk assessment data and generate a comprehensive risk score and justification:
                    
                    Extracted Vendor Information:
                    {extracted_fields}
                    
                    Risk Signals Detected:
                    {risk_signals}
                    
                    External Intelligence Data:
                    {external_intelligence}
                    
                    Based on this information, provide:
                    1. Overall risk score (0-100, where 0 is highest risk)
                    2. Risk level classification (Low/Medium/High/Critical)
                    3. Detailed justification for the score
                    4. Key risk factors identified
                    5. Recommendations for risk mitigation
                    6. Compliance status summary
                    
                    Return the analysis in this JSON format:
                    {{
                        "risk_score": 0-100,
                        "risk_level": "Low/Medium/High/Critical",
                        "justification": "Detailed explanation of the risk assessment",
                        "key_risk_factors": ["Factor 1", "Factor 2"],
                        "recommendations": ["Recommendation 1", "Recommendation 2"],
                        "compliance_status": "Compliant/Non-Compliant/Partial",
                        "confidence_level": "High/Medium/Low"
                    }}
                    """
                )
                
                scoring_chain = LLMChain(llm=self.llm, prompt=scoring_prompt)
                result = scoring_chain.run(
                    extracted_fields=str(extracted_fields),
                    risk_signals=str(risk_signals),
                    external_intelligence=str(external_intelligence)
                )
                
                # Parse the result
                scoring_data = self.parse_scoring_result(result)
                
                # Also run rule-based scoring
                rule_based_score = self.rule_based_scoring(extracted_fields, risk_signals, external_intelligence)
                
                # Combine both results
                final_score = self.combine_scores(scoring_data, rule_based_score)
                
                return final_score
            else:
                # Use rule-based scoring only
                return self.rule_based_scoring(extracted_fields, risk_signals, external_intelligence)
            
        except Exception as e:
            print(f"Error in credibility scoring: {e}")
            return self.rule_based_scoring(
                agent_outputs.get("extracted_fields", {}),
                agent_outputs.get("risk_signals", []),
                agent_outputs.get("external_intelligence", {})
            )
    
    def parse_scoring_result(self, result: str) -> Dict[str, Any]:
        """Parse the LLM scoring result."""
        try:
            # Look for JSON in the result
            if '{' in result and '}' in result:
                start = result.find('{')
                end = result.rfind('}') + 1
                json_str = result[start:end]
                
                import json
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # Fallback parsing
            scoring_data = {
                "risk_level": "Medium",
                "justification": "Analysis completed with standard assessment",
                "key_risk_factors": ["Standard risk assessment"],
                "recommendations": ["Conduct manual review"],
                "compliance_status": "Partial",
                "confidence_level": "Medium"
            }
            
            # Extract score from text
            import re
            score_match = re.search(r'"risk_score":\s*(\d+)', result)
            if score_match:
                scoring_data["risk_score"] = int(score_match.group(1))
            else:
                scoring_data["risk_score"] = 50
                
            # Extract risk level
            if "critical" in result.lower():
                scoring_data["risk_level"] = "Critical"
            elif "high" in result.lower():
                scoring_data["risk_level"] = "High"
            elif "low" in result.lower():
                scoring_data["risk_level"] = "Low"
                
            return scoring_data
            
        except Exception as e:
            print(f"Error parsing scoring result: {e}")
            return {
                "risk_score": 50,
                "risk_level": "Medium",
                "justification": "Error in analysis - manual review required",
                "key_risk_factors": ["Analysis error"],
                "recommendations": ["Manual review required"],
                "compliance_status": "Unknown",
                "confidence_level": "Low"
            }
    
    def rule_based_scoring(self, extracted_fields: Dict[str, Any], risk_signals: List[str], external_intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based scoring using predefined criteria."""
        score = 100
        
        # Deduct points for missing information
        if not extracted_fields.get("PAN"):
            score -= 15
        if not extracted_fields.get("GSTIN"):
            score -= 15
        if not extracted_fields.get("address"):
            score -= 10
        if not extracted_fields.get("bank_details"):
            score -= 10
        if not extracted_fields.get("company_name"):
            score -= 5
        
        # Deduct points for risk signals
        score -= len(risk_signals) * 5
        
        # Consider external intelligence
        mca_status = external_intelligence.get("mca_status", "Not Found")
        gstin_status = external_intelligence.get("gstin_status", "Not Found")
        legal_cases = external_intelligence.get("legal_cases", "Unknown")
        
        if mca_status == "Active":
            score += 10
        elif mca_status == "Inactive":
            score -= 20
        elif mca_status == "Not Found":
            score -= 15
            
        if gstin_status == "Valid":
            score += 10
        elif gstin_status == "Invalid":
            score -= 20
        elif gstin_status == "Not Found":
            score -= 15
            
        if "cases found" in legal_cases.lower():
            score -= 25
        elif "no cases" in legal_cases.lower():
            score += 15
        
        # Determine risk level
        if score >= 80:
            risk_level = "Low"
        elif score >= 60:
            risk_level = "Medium"
        elif score >= 40:
            risk_level = "High"
        else:
            risk_level = "Critical"
        
        # Generate justification
        justification_parts = []
        if score < 100:
            if not extracted_fields.get("PAN"):
                justification_parts.append("Missing PAN")
            if not extracted_fields.get("GSTIN"):
                justification_parts.append("Missing GSTIN")
            if risk_signals:
                justification_parts.append(f"{len(risk_signals)} risk signals detected")
            if mca_status != "Active":
                justification_parts.append(f"MCA status: {mca_status}")
            if gstin_status != "Valid":
                justification_parts.append(f"GSTIN status: {gstin_status}")
        
        justification = f"Risk score {score}/100. " + ". ".join(justification_parts) if justification_parts else f"Risk score {score}/100. No significant issues detected."
        
        return {
            "risk_score": max(0, min(100, score)),
            "risk_level": risk_level,
            "justification": justification,
            "key_risk_factors": risk_signals,
            "recommendations": self.generate_recommendations(score, risk_signals),
            "compliance_status": "Compliant" if score >= 70 else "Non-Compliant" if score < 50 else "Partial",
            "confidence_level": "High" if len(risk_signals) == 0 else "Medium"
        }
    
    def generate_recommendations(self, score: int, risk_signals: List[str]) -> List[str]:
        """Generate recommendations based on score and risk signals."""
        recommendations = []
        
        if score < 50:
            recommendations.append("Immediate manual review required")
            recommendations.append("Consider additional due diligence")
        elif score < 70:
            recommendations.append("Manual verification recommended")
            recommendations.append("Request additional documentation")
        
        if any("PAN" in signal for signal in risk_signals):
            recommendations.append("Verify PAN with income tax department")
        if any("GSTIN" in signal for signal in risk_signals):
            recommendations.append("Verify GSTIN with GST portal")
        if any("address" in signal.lower() for signal in risk_signals):
            recommendations.append("Conduct physical address verification")
        if any("bank" in signal.lower() for signal in risk_signals):
            recommendations.append("Verify bank account details")
        
        if not recommendations:
            recommendations.append("Standard monitoring recommended")
        
        return recommendations
    
    def combine_scores(self, llm_score: Dict[str, Any], rule_score: Dict[str, Any]) -> Dict[str, Any]:
        """Combine LLM and rule-based scores."""
        # Weight the scores (70% LLM, 30% rule-based)
        combined_score = int(llm_score.get("risk_score", 50) * 0.7 + rule_score.get("risk_score", 50) * 0.3)
        
        # Use LLM justification if available, otherwise use rule-based
        justification = llm_score.get("justification") if llm_score.get("justification") != "Analysis not available" else rule_score.get("justification")
        
        # Combine risk factors
        key_risk_factors = list(set(llm_score.get("key_risk_factors", []) + rule_score.get("key_risk_factors", [])))
        
        # Combine recommendations
        recommendations = list(set(llm_score.get("recommendations", []) + rule_score.get("recommendations", [])))
        
        return {
            "risk_score": combined_score,
            "risk_level": llm_score.get("risk_level", rule_score.get("risk_level", "Medium")),
            "justification": justification,
            "key_risk_factors": key_risk_factors,
            "recommendations": recommendations,
            "compliance_status": llm_score.get("compliance_status", rule_score.get("compliance_status", "Partial")),
            "confidence_level": llm_score.get("confidence_level", rule_score.get("confidence_level", "Medium"))
        }
    
    def setup_agent(self):
        """Setup the LangChain agent with tools."""
        if not self.use_gemini:
            return
            
        # Define tools
        self.tools = [
            Tool(
                name="GenerateRiskScore",
                func=self.generate_risk_score,
                description="Aggregates agent outputs to generate a risk score and justification."
            )
        ]
        
        # Define agent prompt
        agent_prompt = PromptTemplate(
            input_variables=["input", "agent_scratchpad"],
            template="""
            You are a credibility scoring agent specialized in aggregating risk assessment data and generating comprehensive vendor risk scores.
            
            Available tools:
            {tools}
            
            Use the following format:
            Question: the input question you must answer
            Thought: you should always think about what to do
            Action: the action to take, should be one of [{tool_names}]
            Action Input: the input to the action
            Observation: the result of the action
            ... (this Thought/Action/Action Input/Observation can repeat N times)
            Thought: I now know the final answer
            Final Answer: the final answer to the original input question
            
            Question: {input}
            {agent_scratchpad}
            """
        )
        
        # Create agent
        self.agent = LLMSingleActionAgent(
            llm_chain=LLMChain(llm=self.llm, prompt=agent_prompt),
            allowed_tools=["GenerateRiskScore"],
            stop=["\nObservation:"],
            handle_parsing_errors=True
        )
        
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            verbose=True
        )
    
    def run(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run the credibility scoring agent."""
        try:
            if self.use_gemini and hasattr(self, 'agent_executor'):
                result = self.agent_executor.run(f"Generate risk score for vendor assessment: {agent_outputs}")
                return self.generate_risk_score(agent_outputs)
            else:
                # Use fallback method
                return self.generate_risk_score(agent_outputs)
        except Exception as e:
            print(f"Agent execution error: {e}")
            return self.generate_risk_score(agent_outputs)

# Create global agent instance
_scoring_agent = None

def get_credibility_scoring_agent() -> CredibilityScoringAgent:
    """Get or create the global credibility scoring agent."""
    global _scoring_agent
    if _scoring_agent is None:
        _scoring_agent = CredibilityScoringAgent()
    return _scoring_agent 