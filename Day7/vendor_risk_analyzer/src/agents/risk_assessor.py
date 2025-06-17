from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Dict
from src.models.vendor import Vendor

class RiskAssessor:
    def __init__(self, google_api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-1.5-pro-latest"
,
            google_api_key=google_api_key,
            temperature=0
        )
        self.tools = self._create_tools()
        self.agent = self._create_agent()
        
    def _create_tools(self) -> List:
        @tool
        def validate_gstin(gstin: str) -> Dict:
            """Validate GSTIN number and check for expiry"""
            # Implement GSTIN validation logic
            return {"is_valid": True, "expiry_date": "2024-12-31"}
            
        @tool
        def check_legal_disputes(vendor_name: str) -> Dict:
            """Check for any legal disputes involving the vendor"""
            # Implement legal dispute checking logic
            return {"has_disputes": False, "disputes": []}
            
        @tool
        def analyze_payment_history(vendor_name: str) -> Dict:
            """Analyze vendor's payment history"""
            # Implement payment history analysis
            return {"payment_score": 85, "issues": []}
            
        return [validate_gstin, check_legal_disputes, analyze_payment_history]
    
    def _create_agent(self) -> AgentExecutor:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a risk assessment expert. Your task is to:
            1. Evaluate vendor risk factors
            2. Check compliance with regulations
            3. Assess financial stability
            4. Provide a comprehensive risk assessment"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    async def assess_risk(self, vendor: Vendor) -> Dict:
        """Assess vendor risk and update risk score"""
        # Prepare input for risk assessment
        input_data = {
            "vendor_name": vendor.name,
            "gstin": vendor.gstin,
            "existing_risk_factors": vendor.risk_factors
        }
        
        # Run risk assessment
        result = await self.agent.ainvoke({
            "input": f"Assess risk for vendor: {input_data}"
        })
        
        # Update vendor risk score based on assessment
        if "risk_factors" in result:
            for factor in result["risk_factors"]:
                vendor.add_risk_factor(factor)
                
        if "risk_score" in result:
            vendor.risk_score = result["risk_score"]
            
        return result 