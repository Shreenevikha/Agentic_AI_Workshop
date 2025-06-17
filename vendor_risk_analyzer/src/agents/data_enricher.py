from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from src.models.vendor import Vendor

class DataEnricher:
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
        def search_mca_database(company_name: str) -> Dict:
            """Search Ministry of Corporate Affairs database for company information"""
            # Implement MCA database search
            return {
                "company_status": "Active",
                "incorporation_date": "2020-01-01",
                "directors": ["John Doe", "Jane Smith"]
            }
            
        @tool
        def validate_pan(pan: str) -> Dict:
            """Validate PAN number and get associated information"""
            # Implement PAN validation
            return {
                "is_valid": True,
                "name": "Example Company",
                "status": "Active"
            }
            
        @tool
        def get_credit_score(vendor_name: str) -> Dict:
            """Get vendor's credit score from credit rating agencies"""
            # Implement credit score retrieval
            return {
                "score": 750,
                "rating": "A",
                "last_updated": "2024-01-01"
            }
            
        return [search_mca_database, validate_pan, get_credit_score]
    
    def _create_agent(self) -> AgentExecutor:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data enrichment expert. Your task is to:
            1. Gather additional information about vendors from public sources
            2. Validate vendor credentials
            3. Enrich vendor profiles with relevant data
            4. Identify potential red flags"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    async def enrich_data(self, vendor: Vendor) -> Dict:
        """Enrich vendor data with information from external sources"""
        # Prepare input for data enrichment
        input_data = {
            "vendor_name": vendor.name,
            "gstin": vendor.gstin,
            "pan": vendor.pan
        }
        
        # Run data enrichment
        result = await self.agent.ainvoke({
            "input": f"Enrich data for vendor: {input_data}"
        })
        
        # Update vendor information with enriched data
        if "company_status" in result:
            if result["company_status"] != "Active":
                vendor.add_risk_factor(f"Company status: {result['company_status']}")
                
        if "credit_score" in result:
            if result["credit_score"] < 600:
                vendor.add_risk_factor(f"Low credit score: {result['credit_score']}")
                
        return result 