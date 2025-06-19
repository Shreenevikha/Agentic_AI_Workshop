"""
Document Analysis Agent
Extracts key risk indicators (PAN, GSTIN, address, bank details) from vendor documents.
"""

from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import AgentAction, AgentFinish
import re
import os
import sys
from typing import List, Dict, Any, Union

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

class DocumentAnalysisAgent:
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
            print("🔄 Using fallback document analysis (rule-based extraction)")
        
    def extract_vendor_fields(self, document_path: str) -> Dict[str, Any]:
        """Extract PAN, GSTIN, address, bank details from the document."""
        try:
            # Read document content
            content = self.read_document(document_path)
            
            if self.use_gemini and self.llm:
                # Use LLM to extract structured information
                extraction_prompt = PromptTemplate(
                    input_variables=["document_content"],
                    template="""
                    Extract the following information from the vendor document:
                    - PAN (Permanent Account Number): 10-character alphanumeric code
                    - GSTIN (Goods and Services Tax Identification Number): 15-character code
                    - Company/Business Address: Full address
                    - Bank Details: Bank name and account number
                    
                    Document Content:
                    {document_content}
                    
                    Return the information in this exact JSON format:
                    {{
                        "PAN": "extracted_pan_or_null",
                        "GSTIN": "extracted_gstin_or_null", 
                        "address": "extracted_address_or_null",
                        "bank_details": "extracted_bank_details_or_null",
                        "company_name": "extracted_company_name_or_null"
                    }}
                    """
                )
                
                extraction_chain = LLMChain(llm=self.llm, prompt=extraction_prompt)
                result = extraction_chain.run(document_content=content)
                
                # Parse JSON result
                import json
                try:
                    extracted_data = json.loads(result)
                    return extracted_data
                except json.JSONDecodeError:
                    # Fallback to regex extraction
                    return self.fallback_extraction(content)
            else:
                # Use fallback extraction
                return self.fallback_extraction(content)
                
        except Exception as e:
            print(f"Error in document analysis: {e}")
            return self.fallback_extraction(content) if 'content' in locals() else {
                'PAN': None,
                'GSTIN': None,
                'address': None,
                'bank_details': None,
                'company_name': None
            }
    
    def read_document(self, file_path: str) -> str:
        """Read document content based on file type."""
        try:
            if file_path.lower().endswith('.pdf'):
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                    return text
            else:
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
        except Exception as e:
            print(f"Error reading document: {e}")
            return ""
    
    def fallback_extraction(self, content: str) -> Dict[str, Any]:
        """Fallback extraction using regex patterns."""
        # PAN pattern: 10 alphanumeric characters
        pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'
        pan_match = re.search(pan_pattern, content.upper())
        
        # GSTIN pattern: 15 characters (2+10+1+1+1)
        gstin_pattern = r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b'
        gstin_match = re.search(gstin_pattern, content.upper())
        
        # Bank account pattern
        bank_pattern = r'\b(?:account|a/c|acc)\s*(?:no|number|#)?\s*:?\s*(\d{9,18})\b'
        bank_match = re.search(bank_pattern, content, re.IGNORECASE)
        
        return {
            'PAN': pan_match.group() if pan_match else None,
            'GSTIN': gstin_match.group() if gstin_match else None,
            'address': self.extract_address(content),
            'bank_details': f"Account: {bank_match.group(1)}" if bank_match else None,
            'company_name': self.extract_company_name(content)
        }
    
    def extract_address(self, content: str) -> str:
        """Extract address using simple heuristics."""
        # Look for address patterns
        address_patterns = [
            r'\b\d+[,\s]+[A-Za-z\s]+(?:street|road|avenue|lane|drive)\b',
            r'\b[A-Za-z\s]+(?:street|road|avenue|lane|drive)[,\s]+\d+\b'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group().strip()
        return None
    
    def extract_company_name(self, content: str) -> str:
        """Extract company name using simple heuristics."""
        # Look for company name patterns
        company_patterns = [
            r'\b[A-Z][A-Za-z\s&]+(?:Ltd|Limited|Inc|Corp|Corporation|Pvt|Private)\b',
            r'\b[A-Z][A-Za-z\s&]+(?:Company|Co|LLC)\b'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group().strip()
        return None
    
    def setup_agent(self):
        """Setup the LangChain agent with tools."""
        if not self.use_gemini:
            return
            
        # Define tools
        self.tools = [
            Tool(
                name="ExtractVendorFields",
                func=self.extract_vendor_fields,
                description="Extracts PAN, GSTIN, address, bank details, and company name from a vendor document."
            )
        ]
        
        # Define agent prompt
        agent_prompt = PromptTemplate(
            input_variables=["input", "agent_scratchpad"],
            template="""
            You are a document analysis agent specialized in extracting vendor information from documents.
            
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
            allowed_tools=["ExtractVendorFields"],
            stop=["\nObservation:"],
            handle_parsing_errors=True
        )
        
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            verbose=True
        )
    
    def run(self, document_path: str) -> Dict[str, Any]:
        """Run the document analysis agent."""
        try:
            if self.use_gemini and hasattr(self, 'agent_executor'):
                result = self.agent_executor.run(f"Analyze the document at {document_path} and extract vendor information")
                return self.extract_vendor_fields(document_path)
            else:
                # Use fallback method
                return self.extract_vendor_fields(document_path)
        except Exception as e:
            print(f"Agent execution error: {e}")
            return self.extract_vendor_fields(document_path)

# Create global agent instance
_document_agent = None

def get_document_analysis_agent() -> DocumentAnalysisAgent:
    """Get or create the global document analysis agent."""
    global _document_agent
    if _document_agent is None:
        _document_agent = DocumentAnalysisAgent()
    return _document_agent 