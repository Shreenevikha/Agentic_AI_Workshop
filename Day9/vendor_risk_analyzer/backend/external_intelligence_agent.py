"""
External Intelligence Agent (RAG)
Fetches external compliance data using Retrieval-Augmented Generation (RAG).
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
from .retriever.retriever_pipeline import get_retriever

class ExternalIntelligenceAgent:
    def __init__(self, llm=None):
        self.llm = llm
        self.use_gemini = config.is_gemini_available()
        self.retriever = get_retriever()
        
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
            print("🔄 Using fallback external intelligence (rule-based analysis)")
        
    def fetch_external_compliance_data(self, vendor_identifiers: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch compliance data from external sources using RAG pipeline."""
        try:
            # Use the RAG retriever to get compliance data
            compliance_data = self.retriever.retrieve_vendor_compliance_data(vendor_identifiers)
            
            # Format retrieved documents for better readability
            formatted_documents = self.format_retrieved_documents(compliance_data.get("retrieved_documents", []))
            
            if self.use_gemini and self.llm:
                # Use LLM to enhance and structure the retrieved data
                enhancement_prompt = PromptTemplate(
                    input_variables=["vendor_info", "retrieved_data"],
                    template="""
                    Analyze the following vendor information and retrieved compliance data to provide comprehensive external intelligence:
                    
                    Vendor Information:
                    {vendor_info}
                    
                    Retrieved Compliance Data:
                    {retrieved_data}
                    
                    Provide a structured analysis including:
                    1. MCA (Ministry of Corporate Affairs) status and details
                    2. GSTIN validation and compliance status
                    3. Legal cases or regulatory issues
                    4. Overall compliance score and risk assessment
                    5. Recommendations for further investigation
                    
                    Return the analysis in this JSON format:
                    {{
                        "mca_status": "Active/Inactive/Not Found",
                        "mca_details": "Additional MCA information",
                        "gstin_status": "Valid/Invalid/Not Found",
                        "gstin_details": "Additional GSTIN information",
                        "legal_cases": "Number and details of legal cases",
                        "regulatory_issues": "Any regulatory compliance issues",
                        "compliance_score": 0-100,
                        "risk_level": "Low/Medium/High",
                        "recommendations": ["Recommendation 1", "Recommendation 2"],
                        "data_sources": ["Source 1", "Source 2"]
                    }}
                    """
                )
                
                enhancement_chain = LLMChain(llm=self.llm, prompt=enhancement_prompt)
                enhanced_result = enhancement_chain.run(
                    vendor_info=str(vendor_identifiers),
                    retrieved_data=str(compliance_data)
                )
                
                # Parse the enhanced result
                enhanced_data = self.parse_enhanced_result(enhanced_result)
                
                # Merge with retrieved data and formatted documents
                final_data = {**compliance_data, **enhanced_data}
                final_data["retrieved_documents"] = formatted_documents
                
                return final_data
            else:
                # Use fallback analysis
                fallback_data = self.fallback_analysis(vendor_identifiers, compliance_data)
                fallback_data["retrieved_documents"] = formatted_documents
                return fallback_data
            
        except Exception as e:
            print(f"Error in external intelligence: {e}")
            # Fallback to basic retrieved data
            basic_data = self.retriever.retrieve_vendor_compliance_data(vendor_identifiers)
            basic_data["retrieved_documents"] = self.format_retrieved_documents(basic_data.get("retrieved_documents", []))
            return basic_data
    
    def format_retrieved_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format retrieved documents for better readability."""
        formatted_docs = []
        
        for i, doc in enumerate(documents, 1):
            # Extract key information from document text
            doc_text = doc.get("document", "")
            metadata = doc.get("metadata", {})
            distance = doc.get("distance", 0)
            
            # Parse document text to extract structured information
            parsed_info = self.parse_document_text(doc_text)
            
            formatted_doc = {
                "rank": i,
                "relevance_score": round((1 - distance) * 100, 2),  # Convert distance to relevance percentage
                "company_name": parsed_info.get("company_name", "Unknown"),
                "pan": parsed_info.get("pan", "Not found"),
                "gstin": parsed_info.get("gstin", "Not found"),
                "mca_status": parsed_info.get("mca_status", "Unknown"),
                "gstin_status": parsed_info.get("gstin_status", "Unknown"),
                "compliance_score": parsed_info.get("compliance_score", "N/A"),
                "summary": parsed_info.get("summary", doc_text),
                "source": metadata.get("source", "Unknown"),
                "date": metadata.get("date", "Unknown"),
                "vendor_id": metadata.get("vendor_id", "Unknown"),
                "raw_document": doc_text,
                "distance": round(distance, 4)
            }
            
            formatted_docs.append(formatted_doc)
        
        return formatted_docs
    
    def parse_document_text(self, doc_text: str) -> Dict[str, Any]:
        """Parse document text to extract structured information."""
        import re
        
        parsed = {
            "company_name": "Unknown",
            "pan": "Not found",
            "gstin": "Not found",
            "mca_status": "Unknown",
            "gstin_status": "Unknown",
            "compliance_score": "N/A",
            "summary": doc_text
        }
        
        # Extract company name (before the first dash)
        if " - " in doc_text:
            parsed["company_name"] = doc_text.split(" - ")[0].strip()
        
        # Extract PAN
        pan_match = re.search(r'PAN:\s*([A-Z0-9]{10})', doc_text)
        if pan_match:
            parsed["pan"] = pan_match.group(1)
        
        # Extract GSTIN
        gstin_match = re.search(r'GSTIN:\s*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})', doc_text)
        if gstin_match:
            parsed["gstin"] = gstin_match.group(1)
        
        # Extract MCA Status
        if "MCA Status: Active" in doc_text:
            parsed["mca_status"] = "Active"
        elif "MCA Status: Inactive" in doc_text:
            parsed["mca_status"] = "Inactive"
        
        # Extract GSTIN Status
        if "GSTIN Status: Valid" in doc_text:
            parsed["gstin_status"] = "Valid"
        elif "GSTIN Status: Invalid" in doc_text:
            parsed["gstin_status"] = "Invalid"
        elif "GSTIN Status: Suspended" in doc_text:
            parsed["gstin_status"] = "Suspended"
        
        # Extract Compliance Score
        score_match = re.search(r'Compliance Score:\s*(\d+)/100', doc_text)
        if score_match:
            parsed["compliance_score"] = score_match.group(1)
        
        # Create summary
        summary_parts = []
        if parsed["company_name"] != "Unknown":
            summary_parts.append(f"Company: {parsed['company_name']}")
        if parsed["mca_status"] != "Unknown":
            summary_parts.append(f"MCA: {parsed['mca_status']}")
        if parsed["gstin_status"] != "Unknown":
            summary_parts.append(f"GSTIN: {parsed['gstin_status']}")
        if parsed["compliance_score"] != "N/A":
            summary_parts.append(f"Score: {parsed['compliance_score']}/100")
        
        if summary_parts:
            parsed["summary"] = " | ".join(summary_parts)
        
        return parsed
    
    def fallback_analysis(self, vendor_identifiers: Dict[str, Any], compliance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis using rule-based methods."""
        # Basic analysis based on retrieved data
        mca_status = compliance_data.get("mca_status", "Not Found")
        gstin_status = compliance_data.get("gstin_status", "Not Found")
        legal_cases = compliance_data.get("legal_cases", "Unknown")
        
        # Determine risk level
        risk_level = "Medium"
        if mca_status == "Active" and gstin_status == "Valid" and "no cases" in legal_cases.lower():
            risk_level = "Low"
        elif mca_status == "Inactive" or gstin_status == "Invalid" or "cases found" in legal_cases.lower():
            risk_level = "High"
        
        # Generate recommendations
        recommendations = []
        if mca_status != "Active":
            recommendations.append("Verify MCA status with corporate affairs ministry")
        if gstin_status != "Valid":
            recommendations.append("Verify GSTIN with GST portal")
        if "cases found" in legal_cases.lower():
            recommendations.append("Review legal cases and regulatory compliance")
        
        if not recommendations:
            recommendations.append("Standard monitoring recommended")
        
        return {
            **compliance_data,
            "mca_details": f"MCA Status: {mca_status}",
            "gstin_details": f"GSTIN Status: {gstin_status}",
            "regulatory_issues": "None identified" if risk_level == "Low" else "Compliance issues detected",
            "risk_level": risk_level,
            "recommendations": recommendations,
            "data_sources": ["RAG System", "Rule-based Analysis"]
        }
    
    def parse_enhanced_result(self, result: str) -> Dict[str, Any]:
        """Parse the LLM enhanced result."""
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
            enhanced_data = {
                "mca_details": "Analysis not available",
                "gstin_details": "Analysis not available",
                "regulatory_issues": "None identified",
                "risk_level": "Medium",
                "recommendations": ["Conduct manual verification"],
                "data_sources": ["RAG System"]
            }
            
            # Extract information from text
            if "active" in result.lower():
                enhanced_data["mca_status"] = "Active"
            elif "inactive" in result.lower():
                enhanced_data["mca_status"] = "Inactive"
            else:
                enhanced_data["mca_status"] = "Not Found"
                
            if "valid" in result.lower():
                enhanced_data["gstin_status"] = "Valid"
            elif "invalid" in result.lower():
                enhanced_data["gstin_status"] = "Invalid"
            else:
                enhanced_data["gstin_status"] = "Not Found"
                
            # Extract compliance score
            import re
            score_match = re.search(r'"compliance_score":\s*(\d+)', result)
            if score_match:
                enhanced_data["compliance_score"] = int(score_match.group(1))
            else:
                enhanced_data["compliance_score"] = 50
                
            return enhanced_data
            
        except Exception as e:
            print(f"Error parsing enhanced result: {e}")
            return {
                "mca_details": "Error in analysis",
                "gstin_details": "Error in analysis",
                "regulatory_issues": "Analysis failed",
                "risk_level": "Unknown",
                "recommendations": ["Manual review required"],
                "data_sources": ["RAG System"],
                "compliance_score": 0
            }
    
    def add_knowledge_base(self, documents: List[str], metadata: List[Dict] = None):
        """Add documents to the knowledge base for RAG."""
        self.retriever.add_knowledge_base(documents, metadata)
    
    def setup_agent(self):
        """Setup the LangChain agent with tools."""
        if not self.use_gemini:
            return
            
        # Define tools
        self.tools = [
            Tool(
                name="FetchExternalComplianceData",
                func=self.fetch_external_compliance_data,
                description="Fetches compliance data from external sources using RAG."
            )
        ]
        
        # Define agent prompt
        agent_prompt = PromptTemplate(
            input_variables=["input", "agent_scratchpad"],
            template="""
            You are an external intelligence agent specialized in gathering compliance and regulatory information about vendors using RAG (Retrieval-Augmented Generation).
            
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
            allowed_tools=["FetchExternalComplianceData"],
            stop=["\nObservation:"],
            handle_parsing_errors=True
        )
        
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            verbose=True
        )
    
    def run(self, vendor_identifiers: Dict[str, Any]) -> Dict[str, Any]:
        """Run the external intelligence agent."""
        try:
            if self.use_gemini and hasattr(self, 'agent_executor'):
                result = self.agent_executor.run(f"Fetch external compliance data for vendor: {vendor_identifiers}")
                return self.fetch_external_compliance_data(vendor_identifiers)
            else:
                # Use fallback method
                return self.fetch_external_compliance_data(vendor_identifiers)
        except Exception as e:
            print(f"Agent execution error: {e}")
            return self.fetch_external_compliance_data(vendor_identifiers)

# Create global agent instance
_external_agent = None

def get_external_intelligence_agent() -> ExternalIntelligenceAgent:
    """Get or create the global external intelligence agent."""
    global _external_agent
    if _external_agent is None:
        _external_agent = ExternalIntelligenceAgent()
    return _external_agent 