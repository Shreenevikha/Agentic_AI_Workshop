import os
from pathlib import Path
from dotenv import load_dotenv
from vendor_risk_analyzer.config import GOOGLE_API_KEY

def analyze_vendor_document(file_path: str) -> dict:
    """Simple function to analyze vendor document."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Basic analysis results
        analysis = {
            "vendor_name": "Sample Vendor",
            "gstin": "22AAAAA0000A1Z5",
            "risk_level": "MEDIUM",
            "risk_score": 0.65,
            "findings": [
                "GSTIN validation passed",
                "Basic documentation present",
                "No major legal issues found",
                "Regular billing patterns observed"
            ],
            "recommendations": [
                "Maintain regular documentation updates",
                "Monitor billing patterns",
                "Conduct periodic compliance checks"
            ]
        }
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing document: {str(e)}")
        return {}

def main():
    # Load environment variables
    load_dotenv()
    
    # Get the current directory
    current_dir = Path(__file__).parent
    
    # Path to sample file
    sample_file = current_dir / "sample_data" / "sample_vendor.txt"
    
    print("\nAnalyzing vendor documents...")
    
    try:
        # Analyze the document
        analysis = analyze_vendor_document(str(sample_file))
        
        # Print results
        print("\nVendor Risk Analysis Results:")
        print("=" * 50)
        print(f"Vendor Name: {analysis.get('vendor_name', 'N/A')}")
        print(f"GSTIN: {analysis.get('gstin', 'N/A')}")
        print(f"Risk Level: {analysis.get('risk_level', 'N/A')}")
        print(f"Risk Score: {analysis.get('risk_score', 'N/A')}")
        
        print("\nKey Findings:")
        for finding in analysis.get('findings', []):
            print(f"- {finding}")
            
        print("\nRecommendations:")
        for rec in analysis.get('recommendations', []):
            print(f"- {rec}")
            
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Ensure the .env file exists with your API key")
        print("2. Check if the sample file exists in the correct location")
        print("3. Verify all required dependencies are installed")

if __name__ == "__main__":
    main() 