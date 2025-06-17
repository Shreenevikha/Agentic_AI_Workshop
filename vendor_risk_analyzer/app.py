import streamlit as st
import os
from pathlib import Path
import json
from datetime import datetime

def analyze_vendor(vendor_name: str, documents: dict) -> dict:
    """Analyze vendor information and documents."""
    # Basic analysis logic
    risk_score = 0.0
    findings = []
    
    # Check GSTIN
    if documents.get("gstin"):
        if len(documents["gstin"]) == 15:
            findings.append("✅ GSTIN format is valid")
        else:
            findings.append("❌ GSTIN format is invalid")
            risk_score += 0.2
    
    # Check documents
    required_docs = ["pan", "registration", "address_proof"]
    for doc in required_docs:
        if documents.get(doc):
            findings.append(f"✅ {doc.replace('_', ' ').title()} document provided")
        else:
            findings.append(f"❌ {doc.replace('_', ' ').title()} document missing")
            risk_score += 0.1
    
    # Check billing history
    if documents.get("billing_history"):
        findings.append("✅ Billing history available")
    else:
        findings.append("❌ No billing history provided")
        risk_score += 0.15
    
    # Determine risk level
    if risk_score <= 0.2:
        risk_level = "LOW"
    elif risk_score <= 0.4:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"
    
    return {
        "vendor_name": vendor_name,
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "findings": findings,
        "recommendations": [
            "Maintain regular documentation updates",
            "Monitor billing patterns",
            "Conduct periodic compliance checks"
        ],
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def main():
    st.set_page_config(page_title="Vendor Risk Analyzer", layout="wide")
    
    st.title("Vendor Risk Analysis System")
    st.markdown("---")
    
    # Input form
    with st.form("vendor_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            vendor_name = st.text_input("Vendor Name")
            gstin = st.text_input("GSTIN Number")
            pan = st.text_input("PAN Number")
            
        with col2:
            registration_date = st.date_input("Registration Date")
            address = st.text_area("Address")
            
        # Document upload section
        st.subheader("Required Documents")
        col3, col4, col5 = st.columns(3)
        
        with col3:
            pan_doc = st.file_uploader("PAN Document", type=['pdf', 'jpg', 'png'])
            registration_doc = st.file_uploader("Registration Document", type=['pdf', 'jpg', 'png'])
            
        with col4:
            address_proof = st.file_uploader("Address Proof", type=['pdf', 'jpg', 'png'])
            billing_history = st.file_uploader("Billing History", type=['pdf', 'xlsx', 'csv'])
            
        with col5:
            other_docs = st.file_uploader("Other Documents", type=['pdf', 'jpg', 'png'], accept_multiple_files=True)
        
        submitted = st.form_submit_button("Analyze Vendor")
    
    if submitted:
        # Collect all documents
        documents = {
            "gstin": gstin,
            "pan": pan,
            "registration_date": str(registration_date),
            "address": address,
            "pan_doc": pan_doc is not None,
            "registration_doc": registration_doc is not None,
            "address_proof": address_proof is not None,
            "billing_history": billing_history is not None,
            "other_docs": len(other_docs) if other_docs else 0
        }
        
        # Perform analysis
        results = analyze_vendor(vendor_name, documents)
        
        # Display results
        st.markdown("---")
        st.subheader("Analysis Results")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Vendor Name", results["vendor_name"])
        with col2:
            st.metric("Risk Score", f"{results['risk_score']:.2f}")
        with col3:
            st.metric("Risk Level", results["risk_level"])
        
        # Findings
        st.subheader("Findings")
        for finding in results["findings"]:
            st.write(finding)
        
        # Recommendations
        st.subheader("Recommendations")
        for rec in results["recommendations"]:
            st.write(f"- {rec}")
        
        # Analysis details
        st.markdown("---")
        st.caption(f"Analysis performed on: {results['analysis_date']}")

if __name__ == "__main__":
    main() 