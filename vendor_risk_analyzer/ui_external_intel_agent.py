import streamlit as st
from vendor_risk_analyzer.agents.external_intelligence_agent import ExternalIntelligenceAgent

st.set_page_config(page_title="External Intelligence Agent", layout="centered")

st.title("🔎 External Intelligence Agent")
st.markdown("""
This tool fetches and summarizes regulatory data for a vendor using RAG (Retrieval-Augmented Generation).

**How to use:**
- Enter the vendor's name, PAN, and/or GSTIN below.
- Click **Fetch Regulatory Data** to get a summary and sources.

---
""")

# Input fields
with st.form("regulatory_form"):
    vendor_name = st.text_input("Vendor Name", placeholder="e.g. Acme Corp")
    pan = st.text_input("PAN", placeholder="e.g. ABCDE1234F")
    gstin = st.text_input("GSTIN", placeholder="e.g. 22AAAAA0000A1Z5")
    submitted = st.form_submit_button("Fetch Regulatory Data")

if submitted:
    with st.spinner("Fetching regulatory data..."):
        agent = ExternalIntelligenceAgent()
        vendor_info = {}
        if vendor_name:
            vendor_info["vendor_name"] = vendor_name
        if pan:
            vendor_info["pan"] = pan
        if gstin:
            vendor_info["gstin"] = gstin
        if not vendor_info:
            st.warning("Please enter at least one field.")
        else:
            result = agent.fetch_regulatory_data(vendor_info)
            st.success("Summary generated!")
            st.markdown("### 📝 Summary")
            st.write(result["summary"])
            st.markdown("### 📚 Sources")
            if result["sources"]:
                for i, meta in enumerate(result["sources"], 1):
                    st.markdown(f"**Source {i}:**")
                    for k, v in meta.items():
                        st.write(f"- {k}: {v}")
            else:
                st.write("No sources found.")

st.markdown("---")
st.caption("Powered by LangChain, ChromaDB, and Google Generative AI") 