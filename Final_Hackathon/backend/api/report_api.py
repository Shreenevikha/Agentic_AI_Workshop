"""
Filing Report Generator API
API endpoints for filing report generation functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
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
        ready_reports = await FilingReport.count({"status": "READY"})
        submitted_reports = await FilingReport.count({"status": "SUBMITTED"})
        draft_reports = await FilingReport.count({"status": "DRAFT"})
        
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
        
        # Get file path
        if file_type.lower() == "json":
            file_path = report.report_data.get("file_paths", {}).get("json")
        elif file_type.lower() == "pdf":
            file_path = report.report_data.get("file_paths", {}).get("pdf")
        else:
            raise HTTPException(status_code=400, detail="Invalid file type. Use 'json' or 'pdf'")
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"{file_type.upper()} file not found")
        
        # In a real implementation, you would return the actual file
        # For now, return file info
        return {
            "success": True,
            "report_id": report_id,
            "file_type": file_type,
            "file_path": file_path,
            "download_url": f"/api/v1/reports/download/{report_id}?file_type={file_type}"
        }
        
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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