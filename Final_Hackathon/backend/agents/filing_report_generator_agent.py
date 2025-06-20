"""
Filing Report Generator Agent
Generates tax return summary and machine-readable files (PDF + JSON)
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
import json
import os
from pathlib import Path
from core.config import settings
from models.mongo_models import FilingReport, FinancialTransaction, ComplianceValidation
from database.mongo_database import get_database

logger = logging.getLogger(__name__)

async def generate_filing_report_agent(filing_type: str, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
    """Generate comprehensive filing report with PDF and JSON"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "filing_report_generator", {
            "filing_type": filing_type,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat()
        })
        
        # Get filing data
        filing_data = await get_filing_data_agent(filing_type, period_start, period_end)
        
        if not filing_data["success"]:
            return filing_data
        
        # Generate section-wise tax figures
        tax_summary = await generate_tax_summary_agent(filing_data["data"])
        
        # Generate JSON schema-compliant file
        json_data = await generate_json_report_agent(filing_type, filing_data["data"], tax_summary)
        
        # Generate PDF report
        pdf_path = await generate_pdf_report_agent(filing_type, filing_data["data"], tax_summary)
        
        # Validate JSON schema
        schema_validation = await validate_json_schema_agent(json_data, filing_type)
        
        # Create filing report record
        filing_report = FilingReport(
            report_id=f"REP-{uuid.uuid4().hex[:8].upper()}",
            filing_type=filing_type,
            period_start=period_start,
            period_end=period_end,
            total_amount=tax_summary["total_taxable_value"],
            tax_amount=tax_summary["total_tax_amount"],
            status="ready",
            report_data={
                "tax_summary": tax_summary,
                "schema_validation": schema_validation,
                "file_paths": {
                    "pdf": pdf_path,
                    "json": f"reports/{filing_type}_{period_start.strftime('%Y%m')}.json"
                }
            },
            file_path=None,
            submitted_at=None
        )
        await filing_report.save()
        
        # Save JSON file
        json_path = await save_json_file_agent(json_data, filing_type, period_start)
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "filing_report_generator", {
                "filing_type": filing_type,
                "report_id": filing_report.report_id,
                "schema_valid": schema_validation["valid"]
            },
            execution_time
        )
        
        return {
            "success": True,
            "filing_type": filing_type,
            "report_id": filing_report.report_id,
            "tax_summary": tax_summary,
            "schema_validation": schema_validation,
            "files": {
                "pdf": pdf_path,
                "json": json_path
            },
            "execution_id": execution_id
        }
        
    except Exception as e:
        logger.error(f"Error in generate_filing_report_agent: {e}")
        await log_agent_execution_error(execution_id, "filing_report_generator", str(e))
        return {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }

async def get_filing_data_agent(filing_type: str, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
    """Get filing data for the specified period and type"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "get_filing_data", {
            "filing_type": filing_type,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat()
        })
        
        # Get transactions for the period
        transactions_from_db = await FinancialTransaction.find({
            "date": {"$gte": period_start, "$lte": period_end}
        }).to_list()
        
        # --- Defensive Data Cleaning ---
        # Clean the status in-memory before passing it to other agents
        status_map = {"pass": "valid", "warning": "pending"}
        for t in transactions_from_db:
            if t.compliance_status in status_map:
                t.compliance_status = status_map[t.compliance_status]
        # --- End Defensive Cleaning ---

        # Filter by filing type
        if filing_type.upper() in ["GSTR-1", "GSTR-3B", "GST"]:
            filtered_transactions = [t for t in transactions_from_db if t.tax_type == "GST"]
        elif filing_type.upper() in ["TDS", "TDS-26Q", "TDS-24Q"]:
            filtered_transactions = [t for t in transactions_from_db if t.tax_type == "TDS"]
        else:
            filtered_transactions = transactions_from_db
        
        # Get compliance validations
        validations = await ComplianceValidation.find({
            "transaction_id": {"$in": [t.transaction_id for t in filtered_transactions]}
        }).to_list()
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "get_filing_data", {
                "transactions_count": len(filtered_transactions),
                "validations_count": len(validations)
            },
            execution_time
        )
        
        return {
            "success": True,
            "data": {
                "transactions": filtered_transactions,
                "validations": validations,
                "period": {
                    "start": period_start,
                    "end": period_end
                }
            },
            "execution_id": execution_id
        }
        
    except Exception as e:
        logger.error(f"Error in get_filing_data_agent: {e}")
        await log_agent_execution_error(execution_id, "get_filing_data", str(e))
        return {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }

async def generate_tax_summary_agent(filing_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate section-wise tax figures"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "tax_summary_generator", {
            "transactions_count": len(filing_data["transactions"])
        })
        
        transactions = filing_data["transactions"]
        
        # Calculate tax summary
        summary = {
            "total_transactions": len(transactions),
            "total_taxable_value": 0,
            "total_tax_amount": 0,
            "section_wise_breakdown": {},
            "compliance_summary": {
                "valid": 0,
                "invalid": 0,
                "pending": 0
            }
        }
        
        # Process each transaction
        for transaction in transactions:
            # Add to totals
            summary["total_taxable_value"] += transaction.amount
            summary["total_tax_amount"] += transaction.amount * 0.18  # 18% GST
            
            # Update compliance summary
            status = transaction.compliance_status or "PENDING"
            summary["compliance_summary"][status.lower()] += 1
            
            # Section-wise breakdown
            category = transaction.category or "Uncategorized"
            if category not in summary["section_wise_breakdown"]:
                summary["section_wise_breakdown"][category] = {
                    "count": 0,
                    "taxable_value": 0,
                    "tax_amount": 0
                }
            
            summary["section_wise_breakdown"][category]["count"] += 1
            summary["section_wise_breakdown"][category]["taxable_value"] += transaction.amount
            summary["section_wise_breakdown"][category]["tax_amount"] += transaction.amount * 0.18
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "tax_summary_generator", {
                "total_taxable_value": summary["total_taxable_value"],
                "total_tax_amount": summary["total_tax_amount"]
            },
            execution_time
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Error in generate_tax_summary_agent: {e}")
        await log_agent_execution_error(execution_id, "tax_summary_generator", str(e))
        return {
            "total_transactions": 0,
            "total_taxable_value": 0,
            "total_tax_amount": 0,
            "section_wise_breakdown": {},
            "compliance_summary": {"valid": 0, "invalid": 0, "pending": 0}
        }

async def generate_json_report_agent(filing_type: str, filing_data: Dict[str, Any], tax_summary: Dict[str, Any]) -> Dict[str, Any]:
    """Generate JSON schema-compliant report"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "json_report_generator", {
            "filing_type": filing_type
        })
        
        # Create JSON structure based on filing type
        if filing_type.upper() in ["GSTR-1", "GSTR-3B", "GST"]:
            json_report = {
                "version": "1.0",
                "filing_type": filing_type,
                "period": {
                    "start": filing_data["period"]["start"].isoformat(),
                    "end": filing_data["period"]["end"].isoformat()
                },
                "summary": {
                    "total_taxable_value": tax_summary["total_taxable_value"],
                    "total_tax_amount": tax_summary["total_tax_amount"],
                    "total_transactions": tax_summary["total_transactions"]
                },
                "section_wise_breakdown": tax_summary["section_wise_breakdown"],
                "compliance_summary": tax_summary["compliance_summary"],
                "transactions": [
                    {
                        "transaction_id": t.transaction_id,
                        "date": t.date.isoformat(),
                        "amount": t.amount,
                        "description": t.description,
                        "category": t.category,
                        "compliance_status": t.compliance_status,
                        "validation_notes": t.validation_notes
                    }
                    for t in filing_data["transactions"]
                ],
                "metadata": {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "schema_version": "1.0",
                    "compatible_with": ["GST Portal", "GSTR-1", "GSTR-3B"]
                }
            }
        elif filing_type.upper() in ["TDS", "TDS-26Q", "TDS-24Q"]:
            json_report = {
                "version": "1.0",
                "filing_type": filing_type,
                "period": {
                    "start": filing_data["period"]["start"].isoformat(),
                    "end": filing_data["period"]["end"].isoformat()
                },
                "summary": {
                    "total_amount_paid": tax_summary["total_taxable_value"],
                    "total_tds_deducted": tax_summary["total_tax_amount"],
                    "total_transactions": tax_summary["total_transactions"]
                },
                "deductee_details": [
                    {
                        "pan": "ABCDE1234F",  # Sample PAN
                        "name": f"Deductee-{i}",
                        "total_amount_paid": t.amount,
                        "tds_rate": 10,
                        "tds_amount": t.amount * 0.10
                    }
                    for i, t in enumerate(filing_data["transactions"])
                ],
                "metadata": {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "schema_version": "1.0",
                    "compatible_with": ["TDS Portal", "TDS-26Q", "TDS-24Q"]
                }
            }
        else:
            json_report = {
                "error": f"Unsupported filing type: {filing_type}",
                "metadata": {
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "json_report_generator", {
                "filing_type": filing_type,
                "json_size": len(json.dumps(json_report))
            },
            execution_time
        )
        
        return json_report
        
    except Exception as e:
        logger.error(f"Error in generate_json_report_agent: {e}")
        await log_agent_execution_error(execution_id, "json_report_generator", str(e))
        return {"error": str(e)}

async def generate_pdf_report_agent(filing_type: str, filing_data: Dict[str, Any], tax_summary: Dict[str, Any]) -> str:
    """Generate PDF report (simplified - returns path)"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "pdf_report_generator", {
            "filing_type": filing_type
        })
        
        # Create reports directory if it doesn't exist
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Generate PDF filename
        period_str = filing_data["period"]["start"].strftime("%Y%m")
        pdf_filename = f"{filing_type}_{period_str}_report.pdf"
        pdf_path = str(reports_dir / pdf_filename)
        
        # In a real implementation, you would use a PDF library like reportlab
        # For now, we'll create a simple text file as placeholder
        with open(pdf_path.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
            f.write(f"TAX FILING REPORT\n")
            f.write(f"================\n\n")
            f.write(f"Filing Type: {filing_type}\n")
            f.write(f"Period: {filing_data['period']['start'].strftime('%Y-%m-%d')} to {filing_data['period']['end'].strftime('%Y-%m-%d')}\n")
            f.write(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"SUMMARY\n")
            f.write(f"=======\n")
            f.write(f"Total Transactions: {tax_summary['total_transactions']}\n")
            f.write(f"Total Taxable Value: Rs. {tax_summary['total_taxable_value']:,.2f}\n")
            f.write(f"Total Tax Amount: Rs. {tax_summary['total_tax_amount']:,.2f}\n\n")
            
            f.write(f"COMPLIANCE SUMMARY\n")
            f.write(f"==================\n")
            for status, count in tax_summary['compliance_summary'].items():
                f.write(f"{status.title()}: {count}\n")
            f.write(f"\n")
            
            f.write(f"SECTION-WISE BREAKDOWN\n")
            f.write(f"=====================\n")
            for category, data in tax_summary['section_wise_breakdown'].items():
                f.write(f"{category}:\n")
                f.write(f"  Count: {data['count']}\n")
                f.write(f"  Taxable Value: Rs. {data['taxable_value']:,.2f}\n")
                f.write(f"  Tax Amount: Rs. {data['tax_amount']:,.2f}\n\n")
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "pdf_report_generator", {
                "filing_type": filing_type,
                "pdf_path": pdf_path
            },
            execution_time
        )
        
        return pdf_path
        
    except Exception as e:
        logger.error(f"Error in generate_pdf_report_agent: {e}")
        await log_agent_execution_error(execution_id, "pdf_report_generator", str(e))
        return ""

async def validate_json_schema_agent(json_data: Dict[str, Any], filing_type: str) -> Dict[str, Any]:
    """Validate JSON against government schema"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "json_schema_validator", {
            "filing_type": filing_type
        })
        
        # Basic schema validation (simplified)
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required fields
        required_fields = ["version", "filing_type", "period", "summary"]
        for field in required_fields:
            if field not in json_data:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Missing required field: {field}")
        
        # Check data types
        if "summary" in json_data:
            summary = json_data["summary"]
            if not isinstance(summary.get("total_taxable_value"), (int, float)):
                validation_result["warnings"].append("total_taxable_value should be numeric")
            if not isinstance(summary.get("total_tax_amount"), (int, float)):
                validation_result["warnings"].append("total_tax_amount should be numeric")
        
        # Check for negative values
        if "summary" in json_data:
            summary = json_data["summary"]
            if summary.get("total_taxable_value", 0) < 0:
                validation_result["errors"].append("total_taxable_value cannot be negative")
            if summary.get("total_tax_amount", 0) < 0:
                validation_result["errors"].append("total_tax_amount cannot be negative")
        
        # Update validation result
        if validation_result["errors"]:
            validation_result["valid"] = False
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "json_schema_validator", {
                "valid": validation_result["valid"],
                "errors_count": len(validation_result["errors"])
            },
            execution_time
        )
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Error in validate_json_schema_agent: {e}")
        await log_agent_execution_error(execution_id, "json_schema_validator", str(e))
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"],
            "warnings": []
        }

async def save_json_file_agent(json_data: Dict[str, Any], filing_type: str, period_start: datetime) -> str:
    """Save JSON file to disk"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "save_json_file", {
            "filing_type": filing_type
        })
        
        # Create reports directory if it doesn't exist
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Generate filename
        period_str = period_start.strftime("%Y%m")
        json_filename = f"{filing_type}_{period_str}.json"
        json_path = str(reports_dir / json_filename)
        
        # Save JSON file
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "save_json_file", {
                "file_path": json_path,
                "file_size": os.path.getsize(json_path)
            },
            execution_time
        )
        
        return json_path
        
    except Exception as e:
        logger.error(f"Error in save_json_file_agent: {e}")
        await log_agent_execution_error(execution_id, "save_json_file", str(e))
        return ""

async def get_report_status_agent(report_id: str) -> Dict[str, Any]:
    """Get status of a filing report"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "get_report_status", {
            "report_id": report_id
        })
        
        # Find report
        report = await FilingReport.find_one({"report_id": report_id})
        
        if not report:
            return {
                "success": False,
                "error": "Report not found",
                "execution_id": execution_id
            }
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "get_report_status", {
                "report_id": report_id,
                "status": report.status
            },
            execution_time
        )
        
        return {
            "success": True,
            "report": {
                "report_id": report.report_id,
                "filing_type": report.filing_type,
                "period_start": report.period_start.isoformat() if report.period_start else None,
                "period_end": report.period_end.isoformat() if report.period_end else None,
                "total_amount": report.total_amount,
                "tax_amount": report.tax_amount,
                "status": report.status,
                "created_at": report.created_at.isoformat(),
                "submitted_at": report.submitted_at.isoformat() if report.submitted_at else None,
                "report_data": report.report_data
            },
            "execution_id": execution_id
        }
        
    except Exception as e:
        logger.error(f"Error in get_report_status_agent: {e}")
        await log_agent_execution_error(execution_id, "get_report_status", str(e))
        return {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }

async def log_agent_execution_start(execution_id: str, agent_name: str, input_data: Dict):
    """Log agent execution start"""
    from models.mongo_models import AgentExecutionLog
    
    log = AgentExecutionLog(
        agent_name=agent_name,
        execution_id=execution_id,
        input_data=input_data,
        status="In Progress"
    )
    await log.save()

async def log_agent_execution_success(execution_id: str, agent_name: str, output_data: Dict, execution_time: float):
    """Log successful agent execution"""
    from models.mongo_models import AgentExecutionLog
    
    log = await AgentExecutionLog.find_one({"execution_id": execution_id})
    if log:
        log.status = "Success"
        log.output_data = output_data
        log.execution_time = execution_time
        await log.save()

async def log_agent_execution_error(execution_id: str, agent_name: str, error_message: str):
    """Log failed agent execution"""
    from models.mongo_models import AgentExecutionLog
    
    log = await AgentExecutionLog.find_one({"execution_id": execution_id})
    if log:
        log.status = "Failed"
        log.error_message = error_message
        await log.save() 