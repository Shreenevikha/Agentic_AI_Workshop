"""
Risk Signal Detection Agent
Analyzes extracted data for anomalies or risk flags (e.g., mismatched GSTINs, missing KYC info).
"""

from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import List, Dict, Any
import re
import sys
import os

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

class RiskSignalAgent:
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
            print("🔄 Using fallback risk signal detection (rule-based analysis)")
        
    def detect_risk_signals(self, extracted_fields: Dict[str, Any]) -> List[str]:
        """Detect anomalies and risk flags in extracted vendor data."""
        try:
            if self.use_gemini and self.llm:
                # Use LLM to analyze risk signals
                risk_analysis_prompt = PromptTemplate(
                    input_variables=["vendor_data"],
                    template="""
                    Analyze the following vendor data for potential risk signals and compliance issues:
                    
                    Vendor Data:
                    {vendor_data}
                    
                    Look for the following risk indicators:
                    1. Missing critical information (PAN, GSTIN, address, bank details)
                    2. Invalid or suspicious PAN/GSTIN formats
                    3. Mismatched information between PAN and GSTIN
                    4. Suspicious address patterns
                    5. Missing company registration details
                    6. Incomplete bank information
                    7. Any other compliance red flags
                    
                    Return a list of risk signals found. If no risks are found, return an empty list.
                    Format: ["Risk 1", "Risk 2", ...]
                    """
                )
                
                risk_chain = LLMChain(llm=self.llm, prompt=risk_analysis_prompt)
                result = risk_chain.run(vendor_data=str(extracted_fields))
                
                # Parse the result
                risks = self.parse_risk_result(result)
                
                # Also run rule-based checks
                rule_based_risks = self.rule_based_risk_detection(extracted_fields)
                
                # Combine both results
                all_risks = list(set(risks + rule_based_risks))
                return all_risks
            else:
                # Use rule-based detection only
                return self.rule_based_risk_detection(extracted_fields)
            
        except Exception as e:
            print(f"Error in risk signal detection: {e}")
            return self.rule_based_risk_detection(extracted_fields)
    
    def parse_risk_result(self, result: str) -> List[str]:
        """Parse the LLM result to extract risk signals."""
        try:
            # Look for list-like patterns in the result
            if '[' in result and ']' in result:
                start = result.find('[')
                end = result.find(']')
                list_str = result[start:end+1]
                
                # Simple parsing - split by commas and clean up
                items = list_str.strip('[]').split(',')
                risks = []
                for item in items:
                    risk = item.strip().strip('"\'')
                    if risk and risk.lower() not in ['none', 'null', '[]']:
                        risks.append(risk)
                return risks
            else:
                # Fallback: look for risk indicators in the text
                risk_indicators = [
                    'missing', 'invalid', 'suspicious', 'mismatched', 
                    'incomplete', 'error', 'risk', 'flag'
                ]
                risks = []
                for indicator in risk_indicators:
                    if indicator in result.lower():
                        # Extract the sentence containing the indicator
                        sentences = result.split('.')
                        for sentence in sentences:
                            if indicator in sentence.lower():
                                risks.append(sentence.strip())
                return risks
        except Exception as e:
            print(f"Error parsing risk result: {e}")
            return []
    
    def rule_based_risk_detection(self, extracted_fields: Dict[str, Any]) -> List[str]:
        """Rule-based risk detection using predefined patterns."""
        risks = []
        
        # Check for missing critical information
        if not extracted_fields.get("PAN"):
            risks.append("Missing PAN (Permanent Account Number)")
        if not extracted_fields.get("GSTIN"):
            risks.append("Missing GSTIN (Goods and Services Tax Identification Number)")
        if not extracted_fields.get("address"):
            risks.append("Missing business address")
        if not extracted_fields.get("bank_details"):
            risks.append("Missing bank account details")
        if not extracted_fields.get("company_name"):
            risks.append("Missing company name")
        
        # Validate PAN format
        pan = extracted_fields.get("PAN")
        if pan:
            pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
            if not re.match(pan_pattern, pan.upper()):
                risks.append(f"Invalid PAN format: {pan}")
        
        # Validate GSTIN format
        gstin = extracted_fields.get("GSTIN")
        if gstin:
            gstin_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
            if not re.match(gstin_pattern, gstin.upper()):
                risks.append(f"Invalid GSTIN format: {gstin}")
        
        # Check for PAN-GSTIN consistency
        if pan and gstin:
            # PAN should be part of GSTIN (positions 3-12)
            pan_in_gstin = gstin[2:12]
            if pan.upper() != pan_in_gstin:
                risks.append("PAN and GSTIN mismatch detected")
        
        # Check for suspicious address patterns
        address = extracted_fields.get("address")
        if address:
            # Check for PO Box or incomplete addresses
            suspicious_patterns = [
                r'p\.?o\.?\s*box',
                r'post\s*office\s*box',
                r'^[a-z\s]+$',  # Only letters and spaces (no numbers)
                r'^\d+\s*$'     # Only numbers
            ]
            for pattern in suspicious_patterns:
                if re.search(pattern, address.lower()):
                    risks.append(f"Suspicious address pattern: {address}")
                    break
        
        # Check for incomplete bank details
        bank_details = extracted_fields.get("bank_details")
        if bank_details:
            # Should contain both bank name and account number
            if not re.search(r'\d{9,18}', bank_details):
                risks.append("Incomplete bank details - missing account number")
            if not re.search(r'\b(?:bank|hdfc|sbi|icici|axis|kotak|yes|idfc)\b', bank_details.lower()):
                risks.append("Incomplete bank details - missing bank name")
        
        return risks
    
    def setup_agent(self):
        """Setup the LangChain agent with tools."""
        if not self.use_gemini:
            return
            
        # Define tools
        self.tools = [
            Tool(
                name="DetectRiskSignals",
                func=self.detect_risk_signals,
                description="Detects anomalies and risk flags in vendor data."
            )
        ]
        
        # Define agent prompt
        agent_prompt = PromptTemplate(
            input_variables=["input", "agent_scratchpad"],
            template="""
            You are a risk signal detection agent specialized in identifying compliance issues and anomalies in vendor data.
            
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
            allowed_tools=["DetectRiskSignals"],
            stop=["\nObservation:"],
            handle_parsing_errors=True
        )
        
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            verbose=True
        )
    
    def run(self, extracted_fields: Dict[str, Any]) -> List[str]:
        """Run the risk signal detection agent."""
        try:
            if self.use_gemini and hasattr(self, 'agent_executor'):
                result = self.agent_executor.run(f"Analyze the following vendor data for risk signals: {extracted_fields}")
                return self.detect_risk_signals(extracted_fields)
            else:
                # Use fallback method
                return self.detect_risk_signals(extracted_fields)
        except Exception as e:
            print(f"Agent execution error: {e}")
            return self.detect_risk_signals(extracted_fields)

# Create global agent instance
_risk_agent = None

def get_risk_signal_agent() -> RiskSignalAgent:
    """Get or create the global risk signal agent."""
    global _risk_agent
    if _risk_agent is None:
        _risk_agent = RiskSignalAgent()
    return _risk_agent 