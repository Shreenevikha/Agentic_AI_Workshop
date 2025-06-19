"""
Vendor Risk Analysis Flow
Defines the agent workflow for vendor risk analysis.
"""

def document_analysis_agent(file_path):
    # Dummy extraction logic
    return {
        "PAN": "ABCDE1234F",
        "GSTIN": "22ABCDE1234F1Z5",
        "address": "123, Main Street, Mumbai",
        "bank_details": "HDFC Bank, A/C: 1234567890"
    }

def risk_signal_detection_agent(extracted_fields):
    risks = []
    if not extracted_fields.get("PAN"):
        risks.append("Missing PAN")
    if not extracted_fields.get("GSTIN"):
        risks.append("Missing GSTIN")
    return risks

def external_intelligence_agent(extracted_fields):
    return {
        "mca_status": "Active",
        "gstin_status": "Valid",
        "legal_cases": "No recent cases found"
    }

def credibility_scoring_agent(risks, external_data):
    score = 100
    if risks:
        score -= 20 * len(risks)
    if external_data.get("legal_cases") != "No recent cases found":
        score -= 30
    justification = "Low risk" if score > 70 else "Medium/High risk"
    return {"score": score, "justification": justification}

def run_vendor_risk_flow(file_path):
    extracted = document_analysis_agent(file_path)
    risks = risk_signal_detection_agent(extracted)
    external = external_intelligence_agent(extracted)
    scoring = credibility_scoring_agent(risks, external)
    return {
        "extracted_fields": extracted,
        "risk_signals": risks,
        "external_intelligence": external,
        "risk_score": scoring["score"],
        "justification": scoring["justification"]
    } 