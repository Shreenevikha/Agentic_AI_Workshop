"""
Main entry point for Vendor Risk Analyzer
Loads vendor documents and runs the risk analysis flow.
"""

from flows.vendor_risk_flow import run_vendor_risk_flow

if __name__ == "__main__":
    # TODO: Load documents from data/ and run the flow
    document_path = "data/sample_vendor.pdf"  # Example
    run_vendor_risk_flow(document_path) 