"""
Configuration for Vendor Risk Analyzer
Includes risk thresholds, weights, and vector store settings.
"""

# Example configuration variables
RISK_THRESHOLDS = {
    'high': 80,
    'medium': 50,
    'low': 20
}

REQUIRED_FIELDS = ['PAN', 'GSTIN', 'address', 'bank_details']

RISK_SIGNAL_WEIGHTS = {
    'missing_pan': 30,
    'mismatched_gstin': 25,
    'missing_kyc': 20
}

VECTOR_STORE_SETTINGS = {
    'type': 'faiss',
    'embedding_dim': 1536
} 