from typing import Dict, List
import logging
from datetime import datetime
import json
import os

class ReportGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Define reports directory relative to where the script is run
        self.reports_dir = os.path.join(os.getcwd(), "reports") 
        self.logger.info(f"Reports directory set to: {self.reports_dir}")
        os.makedirs(self.reports_dir, exist_ok=True) # Ensure directory exists
        self.logger.info(f"Ensured reports directory exists: {self.reports_dir}")

    def generate_report(self, vendor_info: Dict, analysis_results: Dict, risk_score_data: Dict) -> Dict:
        """
        Generates a comprehensive report based on vendor analysis.

        Args:
            vendor_info: Dictionary containing vendor basic information.
            analysis_results: Dictionary containing document and risk analysis results.
            risk_score_data: Dictionary containing the calculated risk score and level.

        Returns:
            Dictionary containing the generated report summary and details.
        """
        report_summary = f"Vendor Risk Analysis Report for {vendor_info.get('name', 'N/A')} (GSTIN: {vendor_info.get('gstin', 'N/A')}).\n"
        report_summary += f"Analysis conducted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.\n\n"

        # Overall Risk Score
        report_summary += f"Overall Credibility Score: {risk_score_data.get('score', 'N/A')} (Risk Level: {risk_score_data.get('risk_level', 'N/A').upper()}).\n\n"

        # Document Analysis Summary
        total_docs = analysis_results.get('document_analysis', {}).get('total_documents', 0)
        report_summary += f"Document Analysis: {total_docs} document(s) were processed.\n"
        for doc in analysis_results.get('document_analysis', {}).get('processed_documents', []):
            report_summary += f"  - {doc.get('metadata', {}).get('filename', 'N/A')} (Extracted Info: {len(doc.get('extracted_info', {}).keys())} categories)\n"
        report_summary += "\n"

        # Risk Analysis Summary
        risk_factors = analysis_results.get('risk_analysis', {}).get('risk_factors', [])
        if risk_factors:
            report_summary += "Identified Risk Factors:\n"
            for factor in risk_factors:
                report_summary += f"  - Category: {factor.get('category', 'N/A')}, Severity: {factor.get('severity', 'N/A').upper()}\n"
                context_cleaned = (factor.get('context', 'N/A')).replace('\n', ' ')
                report_summary += f"    Context: \"{(context_cleaned)[:100]}...\"\n"
        else:
            report_summary += "No significant risk factors identified.\n"
        report_summary += "\n"

        # Component Scores (if available)
        if risk_score_data.get('components'):
            report_summary += "Risk Component Scores:\n"
            for category, score in risk_score_data['components'].items():
                report_summary += f"  - {category.capitalize()}: {score} \n"
            report_summary += "\n"

        # Save the report to a file
        file_name = f"{vendor_info.get('name', 'unknown').replace(' ', '_')}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = os.path.join(self.reports_dir, file_name) # Corrected to self.reports_dir
        self.logger.info(f"Attempting to save report to: {file_path}")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_summary)
            self.logger.info(f"Report successfully saved to {file_path}")
        except Exception as e:
            self.logger.error(f"ERROR: Could not save report to {file_path}: {e}")
            file_path = None # Indicate saving failed

        return {
            "summary": report_summary,
            "file_path": file_path, # Include the file path in the returned dict
            "details": {
                "vendor_info": vendor_info,
                "document_analysis": analysis_results.get('document_analysis'),
                "risk_analysis": analysis_results.get('risk_analysis'),
                "risk_score": risk_score_data
            }
        }

    def _generate_recommendations(self, analysis_results: Dict) -> list:
        """Generate recommendations based on risk analysis"""
        recommendations = []
        risk_level = analysis_results.get("risk_level", "medium")
        risk_factors = analysis_results.get("risk_factors", [])

        # General recommendations based on risk level
        if risk_level == "high":
            recommendations.extend([
                "Conduct detailed due diligence",
                "Request additional documentation",
                "Schedule regular monitoring",
                "Consider phased onboarding"
            ])
        elif risk_level == "medium":
            recommendations.extend([
                "Review specific risk factors",
                "Request clarification on identified issues",
                "Implement standard monitoring"
            ])
        else:  # low
            recommendations.extend([
                "Proceed with standard onboarding",
                "Regular review of vendor status"
            ])

        # Specific recommendations based on risk factors
        for risk in risk_factors:
            if "financial" in risk.get("category", "").lower():
                recommendations.append("Request financial statements and credit reports")
            elif "compliance" in risk.get("category", "").lower():
                recommendations.append("Verify compliance certifications")
            elif "legal" in risk.get("category", "").lower():
                recommendations.append("Review legal documentation with legal team")

        return list(set(recommendations))  # Remove duplicates

    def _save_report(self, report: Dict, vendor_name: str) -> str:
        """Save report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"risk_report_{vendor_name}_{timestamp}.json"
        filepath = os.path.join(self.reports_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        return filepath 