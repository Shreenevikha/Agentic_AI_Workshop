"""
Anomaly Detector Agent
Detects suspicious entries, duplicates, and mismatches in filing data
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from collections import defaultdict
from core.config import settings
from models.mongo_models import FinancialTransaction, Anomaly, ComplianceValidation
from database.mongo_database import get_database, MongoDB

logger = logging.getLogger(__name__)

async def detect_anomalies_agent(transactions: List[FinancialTransaction]) -> Dict[str, Any]:
    """Detect anomalies in transaction data"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "anomaly_detector", {
            "transactions_count": len(transactions)
        })
        
        anomalies = []
        
        # 1. Detect duplicate transactions
        duplicate_anomalies = await detect_duplicate_transactions_agent(transactions)
        anomalies.extend(duplicate_anomalies)
        
        # 2. Detect GSTIN anomalies
        gstin_anomalies = await detect_gstin_anomalies_agent(transactions)
        anomalies.extend(gstin_anomalies)
        
        # 3. Detect amount anomalies
        amount_anomalies = await detect_amount_anomalies_agent(transactions)
        anomalies.extend(amount_anomalies)
        
        # 4. Detect date anomalies
        date_anomalies = await detect_date_anomalies_agent(transactions)
        anomalies.extend(date_anomalies)
        
        # 5. Detect compliance mismatches
        compliance_anomalies = await detect_compliance_mismatches_agent(transactions)
        anomalies.extend(compliance_anomalies)
        
        # Save anomalies to database
        saved_anomalies = []
        if MongoDB.is_connected:
            for anomaly_data in anomalies:
                anomaly = Anomaly(
                    transaction_id=anomaly_data["transaction_id"],
                    anomaly_type=anomaly_data["anomaly_type"].lower(),
                    severity=anomaly_data["severity"].lower(),
                    description=anomaly_data["description"],
                    suggested_fix=anomaly_data["suggested_fix"],
                    status="open",
                    resolved_at=None
                )
                await anomaly.save()
                saved_anomalies.append(anomaly)
            logger.info(f"Saved {len(saved_anomalies)} anomalies to database")
        else:
            logger.info(f"Database not available - keeping {len(anomalies)} anomalies in memory")
            saved_anomalies = anomalies  # Keep in memory for processing
        
        # Categorize anomalies by type
        anomaly_summary = categorize_anomalies(anomalies)
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "anomaly_detector", {
                "anomalies_detected": len(anomalies),
                "anomaly_types": list(anomaly_summary.keys())
            },
            execution_time
        )
        
        return {
            "success": True,
            "anomalies": anomalies,
            "anomaly_summary": anomaly_summary,
            "count": len(anomalies),
            "execution_id": execution_id
        }
        
    except Exception as e:
        logger.error(f"Error in detect_anomalies_agent: {e}")
        await log_agent_execution_error(execution_id, "anomaly_detector", str(e))
        return {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }

async def detect_duplicate_transactions_agent(transactions: List[FinancialTransaction]) -> List[Dict[str, Any]]:
    """Detect duplicate transactions"""
    anomalies = []
    
    # Group transactions by key fields
    transaction_groups = defaultdict(list)
    for transaction in transactions:
        # Create a key based on amount, date, and description
        key = f"{transaction.amount}_{transaction.date.strftime('%Y-%m-%d')}_{transaction.description}"
        transaction_groups[key].append(transaction)
    
    # Find duplicates
    for key, group in transaction_groups.items():
        if len(group) > 1:
            for i, transaction in enumerate(group):
                anomaly = {
                    "transaction_id": transaction.transaction_id,
                    "anomaly_type": "DUPLICATE",
                    "severity": "MEDIUM",
                    "description": f"Duplicate transaction found. {len(group)} transactions with same amount ({transaction.amount}), date ({transaction.date.strftime('%Y-%m-%d')}), and description.",
                    "suggested_fix": "Review and remove duplicate entries. Keep only one transaction if they are truly duplicates."
                }
                anomalies.append(anomaly)
    
    return anomalies

async def detect_gstin_anomalies_agent(transactions: List[FinancialTransaction]) -> List[Dict[str, Any]]:
    """Detect GSTIN-related anomalies"""
    anomalies = []
    
    for transaction in transactions:
        if transaction.tax_type == "GST":
            # Check for missing or invalid GSTIN patterns
            # This is a simplified check - in production, use proper GSTIN validation
            if not hasattr(transaction, 'gstin') or not transaction.gstin:
                anomaly = {
                    "transaction_id": transaction.transaction_id,
                    "anomaly_type": "MISMATCH",
                    "severity": "HIGH",
                    "description": "Missing GSTIN for GST transaction",
                    "suggested_fix": "Add valid GSTIN to the transaction. GSTIN should be 15 characters long."
                }
                anomalies.append(anomaly)
            elif len(str(transaction.gstin)) != 15:
                anomaly = {
                    "transaction_id": transaction.transaction_id,
                    "anomaly_type": "MISMATCH",
                    "severity": "HIGH",
                    "description": f"Invalid GSTIN format: {transaction.gstin}. Expected 15 characters.",
                    "suggested_fix": "Correct the GSTIN format to 15 characters (2 state + 10 PAN + 1 entity + 2 check digits)."
                }
                anomalies.append(anomaly)
    
    return anomalies

async def detect_amount_anomalies_agent(transactions: List[FinancialTransaction]) -> List[Dict[str, Any]]:
    """Detect amount-related anomalies"""
    anomalies = []
    
    # Calculate statistical measures for anomaly detection
    amounts = [t.amount for t in transactions if t.amount > 0]
    if not amounts:
        return anomalies
    
    mean_amount = sum(amounts) / len(amounts)
    threshold = mean_amount * 3  # 3x mean for high-value anomaly
    
    for transaction in transactions:
        # Check for unusually high amounts
        if transaction.amount > threshold:
            anomaly = {
                "transaction_id": transaction.transaction_id,
                "anomaly_type": "SUSPICIOUS",
                "severity": "MEDIUM",
                "description": f"Unusually high amount: ₹{transaction.amount:,.2f} (threshold: ₹{threshold:,.2f})",
                "suggested_fix": "Verify the transaction amount. Consider splitting if it's a legitimate large transaction."
            }
            anomalies.append(anomaly)
        
        # Check for zero or negative amounts
        if transaction.amount <= 0:
            anomaly = {
                "transaction_id": transaction.transaction_id,
                "anomaly_type": "MISMATCH",
                "severity": "HIGH",
                "description": f"Invalid amount: ₹{transaction.amount}",
                "suggested_fix": "Correct the transaction amount to a positive value."
            }
            anomalies.append(anomaly)
    
    return anomalies

async def detect_date_anomalies_agent(transactions: List[FinancialTransaction]) -> List[Dict[str, Any]]:
    """Detect date-related anomalies"""
    anomalies = []
    
    current_date = datetime.now(timezone.utc)
    
    for transaction in transactions:
        # Defensively ensure the transaction date is timezone-aware before comparison
        transaction_date_aware = transaction.date
        if transaction_date_aware.tzinfo is None:
            transaction_date_aware = transaction_date_aware.replace(tzinfo=timezone.utc)

        # Check for future dates
        if transaction_date_aware > current_date:
            anomaly = {
                "transaction_id": transaction.transaction_id,
                "anomaly_type": "SUSPICIOUS",
                "severity": "MEDIUM",
                "description": f"Future date detected: {transaction_date_aware.strftime('%Y-%m-%d')}",
                "suggested_fix": "Correct the transaction date to a past or current date."
            }
            anomalies.append(anomaly)
        
        # Check for very old dates (more than 2 years)
        two_years_ago = current_date.replace(year=current_date.year - 2)
        if transaction_date_aware < two_years_ago:
            anomaly = {
                "transaction_id": transaction.transaction_id,
                "anomaly_type": "SUSPICIOUS",
                "severity": "LOW",
                "description": f"Very old transaction date: {transaction_date_aware.strftime('%Y-%m-%d')}",
                "suggested_fix": "Verify if this transaction should be included in current filing period."
            }
            anomalies.append(anomaly)
    
    return anomalies

async def detect_compliance_mismatches_agent(transactions: List[FinancialTransaction]) -> List[Dict[str, Any]]:
    """Detect compliance-related mismatches"""
    anomalies = []
    
    for transaction in transactions:
        # Check for transactions without compliance validation
        if not transaction.compliance_status or transaction.compliance_status == "PENDING":
            anomaly = {
                "transaction_id": transaction.transaction_id,
                "anomaly_type": "MISMATCH",
                "severity": "HIGH",
                "description": f"Transaction not validated for compliance. Status: {transaction.compliance_status}",
                "suggested_fix": "Run compliance validation on this transaction before filing."
            }
            anomalies.append(anomaly)
        
        # Check for invalid transactions being included
        if transaction.compliance_status == "INVALID":
            anomaly = {
                "transaction_id": transaction.transaction_id,
                "anomaly_type": "MISMATCH",
                "severity": "HIGH",
                "description": f"Invalid transaction included in filing data. Validation notes: {transaction.validation_notes}",
                "suggested_fix": "Fix the compliance issues or exclude this transaction from filing."
            }
            anomalies.append(anomaly)
    
    return anomalies

async def detect_invoice_tds_mismatch_agent(transactions: List[FinancialTransaction]) -> List[Dict[str, Any]]:
    """Detect invoice-TDS mismatches"""
    anomalies = []
    
    # Group transactions by invoice number (simplified)
    invoice_groups = defaultdict(list)
    for transaction in transactions:
        # Extract invoice number from description (simplified)
        if "INV-" in transaction.description:
            invoice_num = transaction.description.split("INV-")[1].split()[0]
            invoice_groups[invoice_num].append(transaction)
    
    # Check for mismatches
    for invoice_num, group in invoice_groups.items():
        gst_transactions = [t for t in group if t.tax_type == "GST"]
        tds_transactions = [t for t in group if t.tax_type == "TDS"]
        
        if gst_transactions and tds_transactions:
            gst_amount = sum(t.amount for t in gst_transactions)
            tds_amount = sum(t.amount for t in tds_transactions)
            
            # Check if TDS amount is reasonable (should be ~10% of GST amount)
            expected_tds = gst_amount * 0.10
            if abs(tds_amount - expected_tds) > expected_tds * 0.5:  # 50% tolerance
                for transaction in group:
                    anomaly = {
                        "transaction_id": transaction.transaction_id,
                        "anomaly_type": "MISMATCH",
                        "severity": "HIGH",
                        "description": f"Invoice-TDS mismatch for invoice {invoice_num}. GST: ₹{gst_amount:,.2f}, TDS: ₹{tds_amount:,.2f}, Expected TDS: ₹{expected_tds:,.2f}",
                        "suggested_fix": "Verify TDS calculation and ensure it matches the expected rate."
                    }
                    anomalies.append(anomaly)
    
    return anomalies

def categorize_anomalies(anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Categorize anomalies by type and severity"""
    summary = {
        "total": len(anomalies),
        "by_type": defaultdict(int),
        "by_severity": defaultdict(int),
        "quick_fixes": []
    }
    
    for anomaly in anomalies:
        summary["by_type"][anomaly["anomaly_type"]] += 1
        summary["by_severity"][anomaly["severity"]] += 1
        
        # Collect unique quick fixes
        if anomaly["suggested_fix"] not in summary["quick_fixes"]:
            summary["quick_fixes"].append(anomaly["suggested_fix"])
    
    return dict(summary)

async def get_anomaly_summary_agent() -> Dict[str, Any]:
    """Get summary of all anomalies"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "anomaly_summary", {})
        
        # Get all anomalies from database
        anomalies = await Anomaly.find({"status": "open"}).to_list()
        
        # Categorize
        summary = categorize_anomalies([
            {
                "anomaly_type": a.anomaly_type,
                "severity": a.severity,
                "suggested_fix": a.suggested_fix
            }
            for a in anomalies
        ])
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "anomaly_summary", {
                "anomalies_count": len(anomalies)
            },
            execution_time
        )
        
        return {
            "success": True,
            "anomaly_summary": summary,
            "anomalies": [
                {
                    "id": str(a.id),
                    "transaction_id": a.transaction_id,
                    "anomaly_type": a.anomaly_type,
                    "severity": a.severity,
                    "description": a.description,
                    "suggested_fix": a.suggested_fix,
                    "status": a.status,
                    "created_at": a.created_at.isoformat()
                }
                for a in anomalies
            ],
            "execution_id": execution_id
        }
        
    except Exception as e:
        logger.error(f"Error in get_anomaly_summary_agent: {e}")
        await log_agent_execution_error(execution_id, "anomaly_summary", str(e))
        return {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }

async def resolve_anomaly_agent(anomaly_id: str, resolution_action: str) -> Dict[str, Any]:
    """Resolve an anomaly"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "resolve_anomaly", {
            "anomaly_id": anomaly_id,
            "resolution_action": resolution_action
        })
        
        # Find and update anomaly
        anomaly = await Anomaly.find_one({"_id": anomaly_id})
        if anomaly:
            if resolution_action == "resolve":
                anomaly.status = "resolved"
                anomaly.resolved_at = datetime.now(timezone.utc)
            elif resolution_action == "ignore":
                anomaly.status = "ignored"
            await anomaly.save()
            
            # Log successful execution
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            await log_agent_execution_success(
                execution_id, "resolve_anomaly", {
                    "anomaly_id": anomaly_id,
                    "resolution_action": resolution_action
                },
                execution_time
            )
            
            return {
                "success": True,
                "anomaly_id": anomaly_id,
                "status": anomaly.status,
                "execution_id": execution_id
            }
        else:
            return {
                "success": False,
                "error": "Anomaly not found",
                "execution_id": execution_id
            }
            
    except Exception as e:
        logger.error(f"Error in resolve_anomaly_agent: {e}")
        await log_agent_execution_error(execution_id, "resolve_anomaly", str(e))
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