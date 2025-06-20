"""
Enhanced Filing Report Generator API
API endpoints for filing report generation with downloadable PDF and JSON files
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os
from pathlib import Path
from agents.filing_report_generator_agent import (
    generate_filing_report_agent,
    get_report_status_agent
)
from models.mongo_models import FilingReport
from database.mongo_database import connect_to_mongo
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

# Pydantic models
class ReportGenerationRequest(BaseModel):
    filing_type: str
    period_start: datetime
    period_end: datetime

class ReportGenerationResponse(BaseModel):
    success: bool
    filing_type: Optional[str] = None
    report_id: Optional[str] = None
    tax_summary: Optional[Dict[str, Any]] = None
    schema_validation: Optional[Dict[str, Any]] = None
    files: Optional[Dict[str, str]] = None
    execution_id: str
    error: Optional[str] = None

class ReportStatusResponse(BaseModel):
    success: bool
    report: Optional[Dict[str, Any]] = None
    execution_id: str
    error: Optional[str] = None

@router.post("/generate", response_model=ReportGenerationResponse)
async def generate_filing_report(request: ReportGenerationRequest):
    """Generate comprehensive filing report with PDF and JSON"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Generate report
        result = await generate_filing_report_agent(
            request.filing_type, request.period_start, request.period_end
        )
        
        if result["success"]:
            return ReportGenerationResponse(
                success=True,
                filing_type=result["filing_type"],
                report_id=result["report_id"],
                tax_summary=result["tax_summary"],
                schema_validation=result["schema_validation"],
                files=result["files"],
                execution_id=result["execution_id"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error generating filing report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}/status", response_model=ReportStatusResponse)
async def get_report_status(report_id: str):
    """Get status of a filing report"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Get report status
        result = await get_report_status_agent(report_id)
        
        if result["success"]:
            return ReportStatusResponse(
                success=True,
                report=result["report"],
                execution_id=result["execution_id"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error getting report status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_reports():
    """List all filing reports"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Get all reports
        reports = await FilingReport.find().sort("created_at", -1).to_list()
        
        return {
            "success": True,
            "reports": [
                {
                    "report_id": report.report_id,
                    "filing_type": report.filing_type,
                    "period_start": report.period_start.isoformat() if report.period_start else None,
                    "period_end": report.period_end.isoformat() if report.period_end else None,
                    "total_amount": report.total_amount,
                    "tax_amount": report.tax_amount,
                    "status": report.status,
                    "created_at": report.created_at.isoformat(),
                    "submitted_at": report.submitted_at.isoformat() if report.submitted_at else None
                }
                for report in reports
            ],
            "count": len(reports)
        }
        
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_reports_summary():
    """Get summary of all reports"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Get summary statistics
        total_reports = await FilingReport.count()
        ready_reports = await FilingReport.count({"status": "ready"})
        submitted_reports = await FilingReport.count({"status": "submitted"})
        draft_reports = await FilingReport.count({"status": "draft"})
        
        # Get total amounts
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_amount": {"$sum": "$total_amount"},
                    "total_tax": {"$sum": "$tax_amount"}
                }
            }
        ]
        
        totals = await FilingReport.aggregate(pipeline).to_list()
        total_amount = totals[0]["total_amount"] if totals else 0
        total_tax = totals[0]["total_tax"] if totals else 0
        
        return {
            "success": True,
            "summary": {
                "total_reports": total_reports,
                "ready_reports": ready_reports,
                "submitted_reports": submitted_reports,
                "draft_reports": draft_reports,
                "total_amount": total_amount,
                "total_tax": total_tax,
                "completion_rate": (ready_reports + submitted_reports) / total_reports * 100 if total_reports > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting reports summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{report_id}")
async def download_report(report_id: str, file_type: str = "json"):
    """Download report file (JSON or PDF)"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Get report
        report = await FilingReport.find_one({"report_id": report_id})
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        if file_type.lower() == "json":
            # Generate JSON report
            json_data = {
                "report_id": report.report_id,
                "filing_type": report.filing_type,
                "period_start": report.period_start.isoformat() if report.period_start else None,
                "period_end": report.period_end.isoformat() if report.period_end else None,
                "total_amount": report.total_amount,
                "tax_amount": report.tax_amount,
                "status": report.status,
                "created_at": report.created_at.isoformat(),
                "submitted_at": report.submitted_at.isoformat() if report.submitted_at else None,
                "tax_summary": report.report_data.get("tax_summary", {}),
                "schema_validation": report.report_data.get("schema_validation", {})
            }
            
            # Create reports directory if it doesn't exist
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            # Save JSON file
            json_filename = f"{report.filing_type}_{report.report_id}.json"
            json_path = reports_dir / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            # Return JSON file
            return FileResponse(
                path=json_path,
                filename=json_filename,
                media_type='application/json'
            )
            
        elif file_type.lower() == "pdf":
            # Generate PDF report
            pdf_filename = f"{report.filing_type}_{report.report_id}.pdf"
            pdf_path = await generate_pdf_report_for_download(report, pdf_filename)
            
            if not pdf_path or not os.path.exists(pdf_path):
                raise HTTPException(status_code=404, detail="PDF file could not be generated")
            
            # Return PDF file
            return FileResponse(
                path=pdf_path,
                filename=pdf_filename,
                media_type='application/pdf'
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid file type. Use 'json' or 'pdf'")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_pdf_report_for_download(report: FilingReport, filename: str) -> str:
    """Generate a professional PDF report for download"""
    try:
        # Try to import ReportLab for PDF generation
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
        except ImportError:
            logger.error("ReportLab not installed. Installing fallback PDF generation...")
            return await generate_simple_pdf_fallback(report, filename)
        
        # Create reports directory if it doesn't exist
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        pdf_path = reports_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("Tax Filing Report", title_style))
        story.append(Spacer(1, 20))
        
        # Report Information
        story.append(Paragraph("Report Information", heading_style))
        
        report_info = [
            ["Report ID:", report.report_id],
            ["Filing Type:", report.filing_type],
            ["Status:", report.status.upper()],
            ["Created Date:", report.created_at.strftime("%B %d, %Y")],
            ["Period Start:", report.period_start.strftime("%B %d, %Y") if report.period_start else "N/A"],
            ["Period End:", report.period_end.strftime("%B %d, %Y") if report.period_end else "N/A"]
        ]
        
        report_table = Table(report_info, colWidths=[2*inch, 4*inch])
        report_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(report_table)
        story.append(Spacer(1, 20))
        
        # Financial Summary
        story.append(Paragraph("Financial Summary", heading_style))
        
        financial_info = [
            ["Total Amount:", f"₹{report.total_amount:,.2f}"],
            ["Tax Amount:", f"₹{report.tax_amount:,.2f}"],
            ["Net Amount:", f"₹{(report.total_amount - report.tax_amount):,.2f}"]
        ]
        
        financial_table = Table(financial_info, colWidths=[2*inch, 4*inch])
        financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(financial_table)
        story.append(Spacer(1, 20))
        
        # Tax Summary Details (if available)
        tax_summary = report.report_data.get("tax_summary", {})
        if tax_summary:
            story.append(Paragraph("Tax Summary Details", heading_style))
            
            # Add tax summary details
            if "section_wise_breakdown" in tax_summary:
                story.append(Paragraph("Section-wise Breakdown:", styles['Heading3']))
                for section, details in tax_summary["section_wise_breakdown"].items():
                    story.append(Paragraph(f"• {section}: ₹{details.get('amount', 0):,.2f}", styles['Normal']))
                story.append(Spacer(1, 10))
        
        # Compliance Summary (if available)
        if "compliance_summary" in tax_summary:
            story.append(Paragraph("Compliance Summary", heading_style))
            compliance = tax_summary["compliance_summary"]
            compliance_info = [
                ["Valid Transactions:", str(compliance.get("valid", 0))],
                ["Invalid Transactions:", str(compliance.get("invalid", 0))],
                ["Pending Transactions:", str(compliance.get("pending", 0))]
            ]
            
            compliance_table = Table(compliance_info, colWidths=[2*inch, 4*inch])
            compliance_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(compliance_table)
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER)
        ))
        
        # Build PDF
        doc.build(story)
        return str(pdf_path)
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        return await generate_simple_pdf_fallback(report, filename)

async def generate_simple_pdf_fallback(report: FilingReport, filename: str) -> str:
    """Fallback PDF generation using simple text-to-PDF conversion"""
    try:
        # Create reports directory if it doesn't exist
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        pdf_path = reports_dir / filename
        
        # Create a simple text-based PDF using fpdf2 if available
        try:
            from fpdf import FPDF
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=16)
            
            # Title
            pdf.cell(200, 10, txt="Tax Filing Report", ln=True, align='C')
            pdf.ln(10)
            
            # Report Information
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Report ID: {report.report_id}", ln=True)
            pdf.cell(200, 10, txt=f"Filing Type: {report.filing_type}", ln=True)
            pdf.cell(200, 10, txt=f"Status: {report.status.upper()}", ln=True)
            pdf.cell(200, 10, txt=f"Created Date: {report.created_at.strftime('%B %d, %Y')}", ln=True)
            pdf.ln(10)
            
            # Financial Summary
            pdf.set_font("Arial", size=14)
            pdf.cell(200, 10, txt="Financial Summary", ln=True)
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Total Amount: ₹{report.total_amount:,.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Tax Amount: ₹{report.tax_amount:,.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Net Amount: ₹{(report.total_amount - report.tax_amount):,.2f}", ln=True)
            
            pdf.output(str(pdf_path))
            return str(pdf_path)
            
        except ImportError:
            # If fpdf2 is not available, create a simple text file
            txt_path = pdf_path.with_suffix('.txt')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("TAX FILING REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Report ID: {report.report_id}\n")
                f.write(f"Filing Type: {report.filing_type}\n")
                f.write(f"Status: {report.status.upper()}\n")
                f.write(f"Created Date: {report.created_at.strftime('%B %d, %Y')}\n")
                f.write(f"Period Start: {report.period_start.strftime('%B %d, %Y') if report.period_start else 'N/A'}\n")
                f.write(f"Period End: {report.period_end.strftime('%B %d, %Y') if report.period_end else 'N/A'}\n\n")
                f.write("FINANCIAL SUMMARY\n")
                f.write("-" * 20 + "\n")
                f.write(f"Total Amount: ₹{report.total_amount:,.2f}\n")
                f.write(f"Tax Amount: ₹{report.tax_amount:,.2f}\n")
                f.write(f"Net Amount: ₹{(report.total_amount - report.tax_amount):,.2f}\n")
            
            return str(txt_path)
            
    except Exception as e:
        logger.error(f"Error in fallback PDF generation: {e}")
        return None

@router.get("/schema-validation/{report_id}")
async def validate_report_schema(report_id: str):
    """Validate report JSON schema"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Get report
        report = await FilingReport.find_one({"report_id": report_id})
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Get schema validation from report data
        schema_validation = report.report_data.get("schema_validation", {})
        
        return {
            "success": True,
            "report_id": report_id,
            "schema_validation": schema_validation,
            "is_valid": schema_validation.get("valid", False)
        }
        
    except Exception as e:
        logger.error(f"Error validating report schema: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 