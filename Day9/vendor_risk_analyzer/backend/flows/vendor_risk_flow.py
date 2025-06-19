"""
Vendor Risk Analysis Flow
Defines the agent workflow for vendor risk analysis using proper LangChain agents.
"""

from typing import Dict, Any
from ..document_analysis_agent import get_document_analysis_agent
from ..risk_signal_agent import get_risk_signal_agent
from ..external_intelligence_agent import get_external_intelligence_agent
from ..credibility_scoring_agent import get_credibility_scoring_agent

def run_vendor_risk_flow(file_path: str) -> Dict[str, Any]:
    """
    Run the complete vendor risk analysis workflow using LangChain agents.
    
    Args:
        file_path: Path to the vendor document to analyze
        
    Returns:
        Dictionary containing the complete risk analysis results
    """
    try:
        print("Starting vendor risk analysis workflow...")
        
        # Step 1: Document Analysis Agent
        print("Step 1: Running Document Analysis Agent...")
        document_agent = get_document_analysis_agent()
        extracted_fields = document_agent.run(file_path)
        print(f"Extracted fields: {extracted_fields}")
        
        # Step 2: Risk Signal Detection Agent
        print("Step 2: Running Risk Signal Detection Agent...")
        risk_agent = get_risk_signal_agent()
        risk_signals = risk_agent.run(extracted_fields)
        print(f"Risk signals detected: {risk_signals}")
        
        # Step 3: External Intelligence Agent (RAG)
        print("Step 3: Running External Intelligence Agent...")
        external_agent = get_external_intelligence_agent()
        external_intelligence = external_agent.run(extracted_fields)
        print(f"External intelligence: {external_intelligence}")
        
        # Step 4: Credibility Scoring Agent
        print("Step 4: Running Credibility Scoring Agent...")
        scoring_agent = get_credibility_scoring_agent()
        
        # Prepare agent outputs for scoring
        agent_outputs = {
            "extracted_fields": extracted_fields,
            "risk_signals": risk_signals,
            "external_intelligence": external_intelligence
        }
        
        scoring_result = scoring_agent.run(agent_outputs)
        print(f"Scoring result: {scoring_result}")
        
        # Compile final results
        final_result = {
            "extracted_fields": extracted_fields,
            "risk_signals": risk_signals,
            "external_intelligence": external_intelligence,
            "risk_score": scoring_result.get("risk_score", 0),
            "risk_level": scoring_result.get("risk_level", "Unknown"),
            "justification": scoring_result.get("justification", "No justification available"),
            "key_risk_factors": scoring_result.get("key_risk_factors", []),
            "recommendations": scoring_result.get("recommendations", []),
            "compliance_status": scoring_result.get("compliance_status", "Unknown"),
            "confidence_level": scoring_result.get("confidence_level", "Low"),
            "workflow_status": "Completed successfully"
        }
        
        print("Vendor risk analysis workflow completed successfully!")
        return final_result
        
    except Exception as e:
        print(f"Error in vendor risk flow: {e}")
        return {
            "error": str(e),
            "workflow_status": "Failed",
            "extracted_fields": {},
            "risk_signals": [],
            "external_intelligence": {},
            "risk_score": 0,
            "risk_level": "Unknown",
            "justification": f"Workflow failed: {str(e)}",
            "key_risk_factors": ["Workflow error"],
            "recommendations": ["Manual review required"],
            "compliance_status": "Unknown",
            "confidence_level": "Low"
        }

# Legacy functions for backward compatibility (now use agents internally)
def document_analysis_agent(file_path):
    """Legacy function - now uses proper LangChain agent."""
    agent = get_document_analysis_agent()
    return agent.run(file_path)

def risk_signal_detection_agent(extracted_fields):
    """Legacy function - now uses proper LangChain agent."""
    agent = get_risk_signal_agent()
    return agent.run(extracted_fields)

def external_intelligence_agent(extracted_fields):
    """Legacy function - now uses proper LangChain agent."""
    agent = get_external_intelligence_agent()
    return agent.run(extracted_fields)

def credibility_scoring_agent(risks, external_data):
    """Legacy function - now uses proper LangChain agent."""
    agent = get_credibility_scoring_agent()
    agent_outputs = {
        "extracted_fields": {},
        "risk_signals": risks,
        "external_intelligence": external_data
    }
    return agent.run(agent_outputs) 