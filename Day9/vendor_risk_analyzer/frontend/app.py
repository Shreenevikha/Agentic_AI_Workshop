# Streamlit frontend entry point 
import streamlit as st
import requests

st.set_page_config(page_title="Vendor Risk Analyzer", layout="centered")
st.title("Vendor Risk Analyzer")
st.write("Upload a vendor document (PDF or text) to analyze risk and credibility.")

# Agent descriptions for popups
agent_descriptions = {
    "Document Analysis Agent": "Parses vendor contracts, invoices, and onboarding forms to extract key risk indicators such as PAN, GSTIN, address, and banking details.",
    "Risk Signal Detection Agent": "Analyzes extracted data for anomalies or risk flags such as mismatched GSTINs, missing KYC info, and irregular payment terms.",
    "External Intelligence Agent": "Implements Retrieval-Augmented Generation (RAG) to pull data from external regulatory sources like MCA databases, GSTIN/PAN registries, and legal case repositories.",
    "Credibility Scoring Agent": "Aggregates insights from all previous agents to generate a vendor risk score and a justification summary, supporting finance team decisions."
}

with st.expander("ℹ️ See Agents Used in Analysis"):
    for agent, desc in agent_descriptions.items():
        if st.button(f"About {agent}", key=agent):
            st.info(desc)

uploaded_file = st.file_uploader("Choose a vendor document", type=["pdf", "txt"])

if uploaded_file:
    st.info(f"Selected file: {uploaded_file.name}")
    if st.button("Analyze Vendor"):
        with st.spinner("Analyzing..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            response = requests.post("http://localhost:8000/analyze/", files=files)
            if response.status_code == 200:
                result = response.json()
                st.success("Analysis Complete!")
                st.markdown("---")
                st.header("📝 Document Analysis Agent")
                with st.expander("Show Extracted Fields"):
                    for k, v in result["extracted_fields"].items():
                        st.write(f"**{k}:** {v}")
                st.header("🚩 Risk Signal Detection Agent")
                with st.expander("Show Risk Signals"):
                    if result["risk_signals"]:
                        for risk in result["risk_signals"]:
                            st.error(risk)
                    else:
                        st.success("No major risk signals detected.")
                st.header("🌐 External Intelligence Agent")
                with st.expander("Show External Intelligence"):
                    # Display basic intelligence info
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric("MCA Status", result["external_intelligence"].get("mca_status", "N/A"))
                    with cols[1]:
                        st.metric("GSTIN Status", result["external_intelligence"].get("gstin_status", "N/A"))
                    with cols[2]:
                        st.metric("Compliance Score", result["external_intelligence"].get("compliance_score", "N/A"))
                    
                    # Display retrieved documents in a neat table format
                    if "retrieved_documents" in result["external_intelligence"]:
                        st.subheader("📑 Retrieved Company Records")
                        docs = result["external_intelligence"]["retrieved_documents"]
                        if isinstance(docs, list):
                            for i, doc in enumerate(docs, 1):
                                with st.container():
                                    st.markdown(f"**Document {i}**")
                                    col1, col2 = st.columns([2, 1])
                                    with col1:
                                        if isinstance(doc, dict):
                                            st.markdown(f"**Company:** {doc.get('company_name', 'N/A')}")
                                            st.markdown(f"**Summary:** {doc.get('summary', 'N/A')}")
                                            st.caption(f"Source: {doc.get('source', 'N/A')} | Date: {doc.get('date', 'N/A')}")
                                    with col2:
                                        if isinstance(doc, dict):
                                            st.metric("Relevance Score", f"{doc.get('relevance_score', 0):.2f}%")
                                    st.markdown("---")
                    
                    # Display other intelligence details
                    st.subheader("🔍 Additional Details")
                    if "regulatory_issues" in result["external_intelligence"]:
                        issues = result["external_intelligence"]["regulatory_issues"]
                        if issues and issues.lower() != "none identified":
                            st.error(f"⚠️ Regulatory Issues: {issues}")
                        else:
                            st.success("✅ No regulatory issues identified")
                    
                    if "risk_level" in result["external_intelligence"]:
                        risk_level = result["external_intelligence"]["risk_level"]
                        risk_color = {
                            "Low": "success",
                            "Medium": "warning",
                            "High": "error"
                        }.get(risk_level, "info")
                        getattr(st, risk_color)(f"Risk Level: {risk_level}")
                st.header("⭐ Credibility Scoring Agent")
                st.metric("Risk Score", result["risk_score"])
                st.info(f"**Justification:** {result['justification']}")
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
else:
    st.info("Please upload a vendor document to begin analysis.")

st.markdown("---")
st.caption("Powered by Agentic AI, LangChain, LangGraph, and FastAPI.") 