"""
Filing Data Aggregator Agent
Prepares filing-ready datasets for each applicable return (GSTR, TDS, etc.)
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import uuid
import json
import csv
from io import StringIO
from core.config import settings
from models.mongo_models import FinancialTransaction, FilingReport, ComplianceValidation
from database.mongo_database import get_database, MongoDB

logger = logging.getLogger(__name__)

async def aggregate_gstr_data_agent(transactions: List[FinancialTransaction], period_start: datetime, period_end: datetime) -> Dict[str, Any]:
    """Aggregate data for GSTR filing"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "gstr_aggregator", {
            "transactions_count": len(transactions),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat()
        })
        
        # Filter transactions for the period, ensuring timezone-aware comparison
        period_transactions = [
            t for t in transactions 
            if period_start.replace(tzinfo=timezone.utc) <= t.date.replace(tzinfo=timezone.utc) <= period_end.replace(tzinfo=timezone.utc) and t.tax_type == "GST"
        ]
        
        # Aggregate by GST categories
        gstr_data = {
            "GSTR-1": {
                "outward_supplies": [],
                "nil_supplies": [],
                "exempt_supplies": [],
                "total_taxable_value": 0,
                "total_tax_amount": 0
            },
            "GSTR-3B": {
                "summary": {
                    "total_taxable_value": 0,
                    "total_tax_amount": 0,
                    "itc_claimed": 0,
                    "net_tax_payable": 0
                }
            }
        }
        
        # Process each transaction
        for transaction in period_transactions:
            if transaction.compliance_status == "VALID":
                # Add to GSTR-1 outward supplies
                supply_data = {
                    "invoice_number": f"INV-{transaction.transaction_id}",
                    "invoice_date": transaction.date.strftime("%d/%m/%Y"),
                    "gstin": "22AAAAA0000A1Z5",  # Sample GSTIN
                    "taxable_value": transaction.amount,
                    "tax_amount": transaction.amount * 0.18,  # 18% GST
                    "total_amount": transaction.amount * 1.18
                }
                gstr_data["GSTR-1"]["outward_supplies"].append(supply_data)
                gstr_data["GSTR-1"]["total_taxable_value"] += transaction.amount
                gstr_data["GSTR-1"]["total_tax_amount"] += transaction.amount * 0.18
        
        # Calculate GSTR-3B summary
        gstr_data["GSTR-3B"]["summary"]["total_taxable_value"] = gstr_data["GSTR-1"]["total_taxable_value"]
        gstr_data["GSTR-3B"]["summary"]["total_tax_amount"] = gstr_data["GSTR-1"]["total_tax_amount"]
        gstr_data["GSTR-3B"]["summary"]["net_tax_payable"] = gstr_data["GSTR-1"]["total_tax_amount"]
        
        # Calculate readiness level
        readiness_level = calculate_readiness_level(gstr_data["GSTR-1"]["outward_supplies"])
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "gstr_aggregator", {
                "transactions_processed": len(period_transactions),
                "readiness_level": readiness_level,
                "total_taxable_value": gstr_data["GSTR-1"]["total_taxable_value"]
            },
            execution_time
        )
        
        return {
            "success": True,
            "gstr_data": gstr_data,
            "readiness_level": readiness_level,
            "summary": {
                "transactions_processed": len(period_transactions),
                "total_taxable_value": gstr_data["GSTR-1"]["total_taxable_value"],
                "total_tax_amount": gstr_data["GSTR-1"]["total_tax_amount"]
            },
            "execution_id": execution_id
        }
        
    except Exception as e:
        logger.error(f"Error in aggregate_gstr_data_agent: {e}")
        await log_agent_execution_error(execution_id, "gstr_aggregator", str(e))
        return {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }

async def aggregate_tds_data_agent(transactions: List[FinancialTransaction], period_start: datetime, period_end: datetime) -> Dict[str, Any]:
    """Aggregate data for TDS filing"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "tds_aggregator", {
            "transactions_count": len(transactions),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat()
        })
        
        # Filter TDS transactions for the period, ensuring timezone-aware comparison
        tds_transactions = [
            t for t in transactions 
            if period_start.replace(tzinfo=timezone.utc) <= t.date.replace(tzinfo=timezone.utc) <= period_end.replace(tzinfo=timezone.utc) and t.tax_type == "TDS"
        ]
        
        # Aggregate TDS data
        tds_data = {
            "deductee_details": [],
            "summary": {
                "total_amount_paid": 0,
                "total_tds_deducted": 0,
                "deductee_count": 0
            }
        }
        
        # Group by deductee (simplified)
        deductee_groups = {}
        for transaction in tds_transactions:
            if transaction.compliance_status == "VALID":
                deductee_pan = "ABCDE1234F"  # Sample PAN
                if deductee_pan not in deductee_groups:
                    deductee_groups[deductee_pan] = {
                        "pan": deductee_pan,
                        "name": f"Deductee-{deductee_pan}",
                        "total_amount": 0,
                        "tds_amount": 0,
                        "transactions": []
                    }
                
                deductee_groups[deductee_pan]["total_amount"] += transaction.amount
                deductee_groups[deductee_pan]["tds_amount"] += transaction.amount * 0.10  # 10% TDS
                deductee_groups[deductee_pan]["transactions"].append(transaction)
        
        # Convert to TDS format
        for deductee in deductee_groups.values():
            tds_data["deductee_details"].append({
                "pan": deductee["pan"],
                "name": deductee["name"],
                "total_amount_paid": deductee["total_amount"],
                "tds_rate": 10,
                "tds_amount": deductee["tds_amount"]
            })
            
            tds_data["summary"]["total_amount_paid"] += deductee["total_amount"]
            tds_data["summary"]["total_tds_deducted"] += deductee["tds_amount"]
        
        tds_data["summary"]["deductee_count"] = len(tds_data["deductee_details"])
        
        # Calculate readiness level
        readiness_level = calculate_readiness_level(tds_data["deductee_details"])
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "tds_aggregator", {
                "transactions_processed": len(tds_transactions),
                "readiness_level": readiness_level,
                "deductee_count": tds_data["summary"]["deductee_count"]
            },
            execution_time
        )
        
        return {
            "success": True,
            "tds_data": tds_data,
            "readiness_level": readiness_level,
            "summary": tds_data["summary"],
            "execution_id": execution_id
        }
        
    except Exception as e:
        logger.error(f"Error in aggregate_tds_data_agent: {e}")
        await log_agent_execution_error(execution_id, "tds_aggregator", str(e))
        return {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }

async def generate_filing_ready_data_agent(filing_type: str, transactions: List[FinancialTransaction], period_start: datetime, period_end: datetime) -> Dict[str, Any]:
    """Generate filing-ready data for any filing type"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "filing_data_generator", {
            "filing_type": filing_type,
            "transactions_count": len(transactions),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat()
        })
        
        # Route to appropriate aggregator
        if filing_type.upper() in ["GSTR-1", "GSTR-3B", "GST"]:
            result = await aggregate_gstr_data_agent(transactions, period_start, period_end)
        elif filing_type.upper() in ["TDS", "TDS-26Q", "TDS-24Q"]:
            result = await aggregate_tds_data_agent(transactions, period_start, period_end)
        else:
            raise ValueError(f"Unsupported filing type: {filing_type}")
        
        if result["success"]:
            # Generate government schema-compliant JSON
            govt_schema_json = generate_government_schema_json(filing_type, result)
            
            # Generate CSV for manual upload
            csv_data = generate_csv_data(filing_type, result)
            
            # Create filing report
            filing_report = FilingReport(
                report_id=f"REP-{uuid.uuid4().hex[:8].upper()}",
                filing_type=filing_type,
                period_start=period_start,
                period_end=period_end,
                total_amount=result["summary"].get("total_taxable_value", 0),
                tax_amount=result["summary"].get("total_tax_amount", 0),
                status="ready",
                report_data=result,
                file_path=None,
                submitted_at=None
            )
            
            # Save to database only if MongoDB is available
            if MongoDB.is_connected:
                await filing_report.save()
                logger.info(f"Saved filing report {filing_report.report_id} to database")
            else:
                logger.info(f"Database not available - keeping filing report {filing_report.report_id} in memory")
            
            # Log successful execution
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            await log_agent_execution_success(
                execution_id, "filing_data_generator", {
                    "filing_type": filing_type,
                    "readiness_level": result["readiness_level"],
                    "report_id": filing_report.report_id
                },
                execution_time
            )
            
            return {
                "success": True,
                "filing_type": filing_type,
                "readiness_level": result["readiness_level"],
                "government_schema_json": govt_schema_json,
                "csv_data": csv_data,
                "report_id": filing_report.report_id,
                "summary": result["summary"],
                "execution_id": execution_id
            }
        else:
            return result
            
    except Exception as e:
        logger.error(f"Error in generate_filing_ready_data_agent: {e}")
        await log_agent_execution_error(execution_id, "filing_data_generator", str(e))
        return {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }

def calculate_readiness_level(data_items: List[Dict]) -> float:
    """Calculate readiness level as percentage"""
    if not data_items:
        return 0.0
    
    # Simple readiness calculation
    # In production, this would check for required fields, validation status, etc.
    total_items = len(data_items)
    valid_items = sum(1 for item in data_items if item)  # Simplified validation
    
    return min(100.0, (valid_items / total_items) * 100) if total_items > 0 else 0.0

def generate_government_schema_json(filing_type: str, result: Dict[str, Any]) -> str:
    """Generate government schema-compliant JSON"""
    if filing_type.upper() in ["GSTR-1", "GSTR-3B", "GST"]:
        # GSTR schema
        schema_data = {
            "version": "1.0",
            "filing_type": filing_type,
            "period": {
                "start": result.get("summary", {}).get("period_start", ""),
                "end": result.get("summary", {}).get("period_end", "")
            },
            "summary": result.get("summary", {}),
            "details": result.get("gstr_data", {})
        }
    elif filing_type.upper() in ["TDS", "TDS-26Q", "TDS-24Q"]:
        # TDS schema
        schema_data = {
            "version": "1.0",
            "filing_type": filing_type,
            "period": {
                "start": result.get("summary", {}).get("period_start", ""),
                "end": result.get("summary", {}).get("period_end", "")
            },
            "summary": result.get("summary", {}),
            "deductee_details": result.get("tds_data", {}).get("deductee_details", [])
        }
    else:
        schema_data = {"error": "Unsupported filing type"}
    
    return json.dumps(schema_data, indent=2)

def generate_csv_data(filing_type: str, result: Dict[str, Any]) -> str:
    """Generate CSV data for manual upload"""
    output = StringIO()
    writer = csv.writer(output)
    
    if filing_type.upper() in ["GSTR-1", "GSTR-3B", "GST"]:
        # GSTR CSV headers
        writer.writerow(["Invoice Number", "Invoice Date", "GSTIN", "Taxable Value", "Tax Amount", "Total Amount"])
        
        # GSTR data
        for supply in result.get("gstr_data", {}).get("GSTR-1", {}).get("outward_supplies", []):
            writer.writerow([
                supply.get("invoice_number", ""),
                supply.get("invoice_date", ""),
                supply.get("gstin", ""),
                supply.get("taxable_value", 0),
                supply.get("tax_amount", 0),
                supply.get("total_amount", 0)
            ])
            
    elif filing_type.upper() in ["TDS", "TDS-26Q", "TDS-24Q"]:
        # TDS CSV headers
        writer.writerow(["PAN", "Name", "Total Amount Paid", "TDS Rate", "TDS Amount"])
        
        # TDS data
        for deductee in result.get("tds_data", {}).get("deductee_details", []):
            writer.writerow([
                deductee.get("pan", ""),
                deductee.get("name", ""),
                deductee.get("total_amount_paid", 0),
                deductee.get("tds_rate", 0),
                deductee.get("tds_amount", 0)
            ])
    
    return output.getvalue()

async def get_filing_readiness_summary_agent() -> Dict[str, Any]:
    """Get summary of all filing readiness levels"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "filing_readiness_summary", {})
        
        # Get current period
        now = datetime.now(timezone.utc)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        # Get all transactions for the period
        transactions = await FinancialTransaction.find({
            "date": {"$gte": period_start, "$lte": period_end}
        }).to_list()
        
        # Calculate readiness for each filing type
        filing_types = ["GSTR-1", "GSTR-3B", "TDS-26Q"]
        readiness_summary = {}
        
        for filing_type in filing_types:
            result = await generate_filing_ready_data_agent(filing_type, transactions, period_start, period_end)
            if result["success"]:
                readiness_summary[filing_type] = {
                    "readiness_level": result["readiness_level"],
                    "status": "Ready" if result["readiness_level"] >= 80 else "Needs Review",
                    "summary": result["summary"]
                }
            else:
                readiness_summary[filing_type] = {
                    "readiness_level": 0,
                    "status": "Error",
                    "error": result["error"]
                }
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "filing_readiness_summary", {
                "filing_types_checked": len(filing_types),
                "period": f"{period_start.strftime('%B %Y')}"
            },
            execution_time
        )
        
        return {
            "success": True,
            "readiness_summary": readiness_summary,
            "period": f"{period_start.strftime('%B %Y')}",
            "execution_id": execution_id
        }
        
    except Exception as e:
        logger.error(f"Error in get_filing_readiness_summary_agent: {e}")
        await log_agent_execution_error(execution_id, "filing_readiness_summary", str(e))
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