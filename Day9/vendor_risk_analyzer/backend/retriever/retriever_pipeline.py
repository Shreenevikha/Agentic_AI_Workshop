"""
Retriever Pipeline
Handles embedding, storage, and retrieval of external knowledge for RAG.
"""

import openai
from typing import List, Dict, Any
import os
import sys
import numpy as np

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import config
from .vector_store import VectorStore, initialize_vector_store

class RAGRetriever:
    def __init__(self, gemini_api_key: str = None):
        self.gemini_api_key = gemini_api_key or config.gemini_api_key
        self.use_gemini = config.is_gemini_available() and self.gemini_api_key
        
        if self.use_gemini:
            openai.api_key = self.gemini_api_key
            print("✅ OpenAI API configured for RAG system")
        else:
            print("🔄 Using fallback RAG system (rule-based retrieval)")
            
        self.vector_store = initialize_vector_store()
        
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a text using OpenAI or fallback."""
        if self.use_gemini:
            try:
                response = openai.Embedding.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                return response['data'][0]['embedding']
            except Exception as e:
                print(f"Error getting embedding: {e}")
                # Return zero vector as fallback
                return [0.0] * 1536
        else:
            # Fallback: simple hash-based embedding
            return self.fallback_embedding(text)
    
    def fallback_embedding(self, text: str) -> List[float]:
        """Generate a simple embedding using text characteristics."""
        # Create a simple embedding based on text characteristics
        embedding = [0.0] * 1536
        
        # Use character frequency and text length
        text_lower = text.lower()
        char_freq = {}
        for char in text_lower:
            if char.isalnum():
                char_freq[char] = char_freq.get(char, 0) + 1
        
        # Fill embedding based on character frequency
        for i, (char, freq) in enumerate(char_freq.items()):
            if i < 1536:
                embedding[i] = min(freq / len(text), 1.0)
        
        # Add text length information
        if len(embedding) > 0:
            embedding[0] = min(len(text) / 1000, 1.0)
        
        return embedding
    
    def add_knowledge_base(self, documents: List[str], metadata: List[Dict] = None):
        """Add documents to the knowledge base."""
        embeddings = [self.get_embedding(doc) for doc in documents]
        self.vector_store.add_documents(documents, embeddings, metadata)
    
    def retrieve_external_knowledge(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant external knowledge for a given query."""
        query_embedding = self.get_embedding(query)
        results = self.vector_store.search(query_embedding, k)
        return results
    
    def retrieve_vendor_compliance_data(self, vendor_info: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve compliance data for a specific vendor."""
        # Create query from vendor information
        query_parts = []
        if vendor_info.get("PAN"):
            query_parts.append(f"PAN: {vendor_info['PAN']}")
        if vendor_info.get("GSTIN"):
            query_parts.append(f"GSTIN: {vendor_info['GSTIN']}")
        if vendor_info.get("company_name"):
            query_parts.append(f"Company: {vendor_info['company_name']}")
            
        query = " ".join(query_parts) if query_parts else "vendor compliance data"
        
        # Retrieve relevant documents
        results = self.retrieve_external_knowledge(query, k=3)
        
        # Process and structure the results
        compliance_data = {
            "mca_status": "Not found",
            "gstin_status": "Not found", 
            "legal_cases": "No cases found",
            "compliance_score": 0,
            "retrieved_documents": results
        }
        
        # Extract information from retrieved documents
        for result in results:
            doc_text = result["document"].lower()
            if "active" in doc_text and "mca" in doc_text:
                compliance_data["mca_status"] = "Active"
            if "valid" in doc_text and "gstin" in doc_text:
                compliance_data["gstin_status"] = "Valid"
            if "case" in doc_text or "legal" in doc_text:
                compliance_data["legal_cases"] = "Cases found"
                
        # Calculate compliance score
        score = 100
        if compliance_data["mca_status"] == "Active":
            score += 20
        if compliance_data["gstin_status"] == "Valid":
            score += 20
        if compliance_data["legal_cases"] == "No cases found":
            score += 30
        else:
            score -= 30
            
        compliance_data["compliance_score"] = max(0, min(100, score))
        
        return compliance_data

# Global retriever instance
_retriever = None

def get_retriever() -> RAGRetriever:
    """Get or create the global retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
    return _retriever

def retrieve_external_knowledge(query: str):
    """Retrieve relevant external knowledge for a given query."""
    retriever = get_retriever()
    return retriever.retrieve_external_knowledge(query) 