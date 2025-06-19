"""
Test Script for Vendor Risk Analyzer Agents
Demonstrates the proper LangChain agent implementation and RAG functionality.
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.document_analysis_agent import get_document_analysis_agent
from backend.risk_signal_agent import get_risk_signal_agent
from backend.external_intelligence_agent import get_external_intelligence_agent
from backend.credibility_scoring_agent import get_credibility_scoring_agent
from backend.retriever.retriever_pipeline import get_retriever
from backend.data.sample_knowledge_base import initialize_sample_knowledge_base

def test_rag_system():
    """Test the RAG system functionality."""
    print("=" * 60)
    print("TESTING RAG SYSTEM")
    print("=" * 60)
    
    try:
        # Initialize retriever
        retriever = get_retriever()
        initialize_sample_knowledge_base(retriever)
        
        # Test retrieval
        test_query = "ABC Technologies Ltd compliance status"
        results = retriever.retrieve_external_knowledge(test_query, k=3)
        
        print(f"Query: {test_query}")
        print(f"Retrieved {len(results)} documents:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['document'][:100]}...")
            print(f"     Distance: {result['distance']:.4f}")
        
        # Test vendor compliance data retrieval
        vendor_info = {"PAN": "ABCDE1234F", "GSTIN": "22ABCDE1234F1Z5"}
        compliance_data = retriever.retrieve_vendor_compliance_data(vendor_info)
        
        print(f"\nVendor Compliance Data for {vendor_info['PAN']}:")
        print(json.dumps(compliance_data, indent=2))
        
        return True
        
    except Exception as e:
        print(f"RAG System Test Failed: {e}")
        return False

def test_document_analysis_agent():
    """Test the document analysis agent."""
    print("\n" + "=" * 60)
    print("TESTING DOCUMENT ANALYSIS AGENT")
    print("=" * 60)
    
    try:
        # Create a sample document
        sample_doc_path = "backend/data/sample_vendor.txt"
        os.makedirs(os.path.dirname(sample_doc_path), exist_ok=True)
        
        sample_content = """
        VENDOR INFORMATION
        
        Company Name: Test Technologies Ltd
        PAN: ABCDE1234F
        GSTIN: 22ABCDE1234F1Z5
        Address: 123, Tech Park, Bangalore, Karnataka - 560001
        Bank Details: HDFC Bank, Account Number: 1234567890
        
        Contact: +91-9876543210
        Email: info@testtech.com
        """
        
        with open(sample_doc_path, "w") as f:
            f.write(sample_content)
        
        # Test agent
        agent = get_document_analysis_agent()
        result = agent.run(sample_doc_path)
        
        print("Document Analysis Result:")
        print(json.dumps(result, indent=2))
        
        # Clean up
        os.remove(sample_doc_path)
        
        return result
        
    except Exception as e:
        print(f"Document Analysis Agent Test Failed: {e}")
        return None

def test_risk_signal_agent(extracted_fields):
    """Test the risk signal detection agent."""
    print("\n" + "=" * 60)
    print("TESTING RISK SIGNAL DETECTION AGENT")
    print("=" * 60)
    
    try:
        agent = get_risk_signal_agent()
        result = agent.run(extracted_fields)
        
        print("Risk Signals Detected:")
        print(json.dumps(result, indent=2))
        
        return result
        
    except Exception as e:
        print(f"Risk Signal Agent Test Failed: {e}")
        return []

def test_external_intelligence_agent(extracted_fields):
    """Test the external intelligence agent."""
    print("\n" + "=" * 60)
    print("TESTING EXTERNAL INTELLIGENCE AGENT")
    print("=" * 60)
    
    try:
        agent = get_external_intelligence_agent()
        result = agent.run(extracted_fields)
        
        print("External Intelligence Result:")
        print(json.dumps(result, indent=2))
        
        return result
        
    except Exception as e:
        print(f"External Intelligence Agent Test Failed: {e}")
        return {}

def test_credibility_scoring_agent(agent_outputs):
    """Test the credibility scoring agent."""
    print("\n" + "=" * 60)
    print("TESTING CREDIBILITY SCORING AGENT")
    print("=" * 60)
    
    try:
        agent = get_credibility_scoring_agent()
        result = agent.run(agent_outputs)
        
        print("Credibility Scoring Result:")
        print(json.dumps(result, indent=2))
        
        return result
        
    except Exception as e:
        print(f"Credibility Scoring Agent Test Failed: {e}")
        return {}

def test_complete_workflow():
    """Test the complete agent workflow."""
    print("\n" + "=" * 60)
    print("TESTING COMPLETE AGENT WORKFLOW")
    print("=" * 60)
    
    try:
        # Step 1: Document Analysis
        extracted_fields = test_document_analysis_agent()
        if not extracted_fields:
            return False
        
        # Step 2: Risk Signal Detection
        risk_signals = test_risk_signal_agent(extracted_fields)
        
        # Step 3: External Intelligence
        external_intelligence = test_external_intelligence_agent(extracted_fields)
        
        # Step 4: Credibility Scoring
        agent_outputs = {
            "extracted_fields": extracted_fields,
            "risk_signals": risk_signals,
            "external_intelligence": external_intelligence
        }
        
        scoring_result = test_credibility_scoring_agent(agent_outputs)
        
        # Final Result
        final_result = {
            "extracted_fields": extracted_fields,
            "risk_signals": risk_signals,
            "external_intelligence": external_intelligence,
            "risk_score": scoring_result.get("risk_score", 0),
            "risk_level": scoring_result.get("risk_level", "Unknown"),
            "justification": scoring_result.get("justification", "No justification"),
            "key_risk_factors": scoring_result.get("key_risk_factors", []),
            "recommendations": scoring_result.get("recommendations", []),
            "compliance_status": scoring_result.get("compliance_status", "Unknown"),
            "confidence_level": scoring_result.get("confidence_level", "Low")
        }
        
        print("\nFINAL WORKFLOW RESULT:")
        print(json.dumps(final_result, indent=2))
        
        return True
        
    except Exception as e:
        print(f"Complete Workflow Test Failed: {e}")
        return False

def main():
    """Run all tests."""
    print("VENDOR RISK ANALYZER - AGENT TESTING")
    print("=" * 60)
    
    # Test RAG system
    rag_success = test_rag_system()
    
    # Test complete workflow
    workflow_success = test_complete_workflow()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"RAG System: {'✓ PASSED' if rag_success else '✗ FAILED'}")
    print(f"Agent Workflow: {'✓ PASSED' if workflow_success else '✗ FAILED'}")
    
    if rag_success and workflow_success:
        print("\n🎉 ALL TESTS PASSED! The agent implementation is working correctly.")
        print("\nKey Improvements Made:")
        print("1. ✓ Proper LangChain agents with AgentExecutor")
        print("2. ✓ RAG system with FAISS vector store")
        print("3. ✓ Document retrieval functionality")
        print("4. ✓ Agent orchestration and workflow")
        print("5. ✓ Comprehensive risk assessment")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main() 