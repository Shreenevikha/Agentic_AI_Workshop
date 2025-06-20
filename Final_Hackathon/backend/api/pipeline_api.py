"""
Pipeline Orchestration API
Runs the full multi-agent compliance pipeline and returns dashboard data
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import csv
import io
import asyncio
import pandas as pd
from agents.regulation_fetcher_agent import fetch_regulations_agent
from agents.compliance_validator_agent import validate_batch_transactions_agent
from agents.filing_data_aggregator_agent import generate_filing_ready_data_agent
from agents.anomaly_detector_agent import detect_anomalies_agent
from agents.filing_report_generator_agent import generate_filing_report_agent
from models.mongo_models import FinancialTransaction
from database.mongo_database import connect_to_mongo, MongoDB
from api.filing_api import in_memory_transactions
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])

class PipelineRunResponse(BaseModel):
    success: bool
    compliance_summary: Optional[Dict[str, Any]] = None
    flagged_entries: Optional[List[Dict[str, Any]]] = None
    filing_summary: Optional[Dict[str, Any]] = None
    anomalies: Optional[List[Dict[str, Any]]] = None
    report: Optional[Dict[str, Any]] = None
    dashboard: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/run", response_model=PipelineRunResponse)
async def run_pipeline(
    domain: str = Form(...),
    entity_type: str = Form(...),
    filing_type: str = Form(...),
    # The form dates are now optional and will be overridden by file content
    period_start_form: Optional[datetime] = Form(None, alias="period_start"),
    period_end_form: Optional[datetime] = Form(None, alias="period_end"),
    file: Optional[UploadFile] = File(None)
):
    """
    Run the full compliance pipeline.
    This will automatically detect the date range from the file if provided.
    """
    try:
        await connect_to_mongo()
        
        # --- Start of New Data Sanitization Step ---
        if MongoDB.is_connected:
            # Sanitize 'warning' status
            await FinancialTransaction.find(
                {"compliance_status": "warning"}
            ).update({"$set": {"compliance_status": "pending"}})
            
            # Sanitize 'pass' status
            await FinancialTransaction.find(
                {"compliance_status": "pass"}
            ).update({"$set": {"compliance_status": "valid"}})
            
            logger.info("Sanitized any existing transactions with legacy status values.")
        # --- End of New Data Sanitization Step ---
        
        transactions = []
        period_start = None
        period_end = None

        if file:
            content = await file.read()
            df = pd.read_csv(io.BytesIO(content))
            
            # --- Final Robust Date Parsing Logic ---
            if 'date' in df.columns:
                # Use flexible date parsing and immediately drop rows that fail
                df['date'] = pd.to_datetime(
                    df['date'], 
                    errors='coerce', 
                    infer_datetime_format=True
                )
                df.dropna(subset=['date'], inplace=True)
                
                # If all rows were dropped, it means no valid dates were found.
                if df.empty:
                    logger.error("Could not parse any valid dates from the uploaded CSV.")
                    return PipelineRunResponse(success=False, error="Could not read any valid dates from the file. Please ensure the 'date' column is formatted correctly (e.g., YYYY-MM-DD, DD/MM/YYYY).")

                period_start = df['date'].min().to_pydatetime()
                period_end = df['date'].max().to_pydatetime()
                logger.info(f"Processing all transactions from file within detected range: {period_start.date()} to {period_end.date()}")
            else:
                return PipelineRunResponse(success=False, error="The uploaded CSV file must contain a 'date' column.")
            # --- End of Final Logic ---

            for index, row in df.iterrows():
                try:
                    transaction_date = row['date']
                    if transaction_date.tzinfo is None:
                        transaction_date = transaction_date.tz_localize('UTC')
                    else:
                        transaction_date = transaction_date.tz_convert('UTC')

                    transaction_data = {
                        "transaction_id": str(row.get('transaction_id') or hash(f"{row.get('date', '')}{row.get('description', '')}{row.get('amount', '')}{index}")),
                        "date": transaction_date,
                        "description": str(row.get('description', '')),
                        "amount": float(row['amount']),
                        "category": str(row.get('category', '')),
                        "vendor": str(row.get('vendor', '')),
                        "is_debit": bool(row.get('is_debit', True)),
                        "tags": str(row.get('tags', '')).split(',') if isinstance(row.get('tags'), str) else [],
                        "tax_type": str(row.get('tax_type', '')),
                        "compliance_status": "pending",
                        "validation_notes": ""
                    }
                    
                    transaction = FinancialTransaction(**transaction_data)
                    
                    if MongoDB.is_connected:
                        await transaction.save()
                    transactions.append(transaction)
                except Exception as e:
                    logger.error(f"Error processing row {index} from CSV. Data: {row}. Error: {e}")
                    continue
        else:
            # Fallback to form dates if no file is uploaded
            period_start = period_start_form
            period_end = period_end_form
            
            if not period_start or not period_end:
                 return PipelineRunResponse(success=False, error="Date range must be provided when no file is uploaded.")

            if MongoDB.is_connected:
                transactions = await FinancialTransaction.find({
                    "date": {"$gte": period_start, "$lte": period_end}
                }).to_list()
            else:
                transactions = [
                    t for t in in_memory_transactions 
                    if period_start <= t.date.replace(tzinfo=timezone.utc) <= period_end
                ]
                logger.info(f"Using {len(transactions)} in-memory transactions for pipeline")

        if not transactions:
            # This check is now primarily for the no-file scenario
            return PipelineRunResponse(success=False, error="No transactions found. Please upload a CSV file or ensure the database contains data for the selected period.")
        
        # Ensure period_start and period_end are valid for the agents
        if not period_start or not period_end:
            # Fallback if dates couldn't be determined from the file
            period_start = datetime.now(timezone.utc) - timedelta(days=30)
            period_end = datetime.now(timezone.utc)
            
        if period_start.tzinfo is None:
            period_start = period_start.replace(tzinfo=timezone.utc)
        if period_end.tzinfo is None:
            period_end = period_end.replace(tzinfo=timezone.utc)
        
        logger.info(f"Running pipeline with final period: {period_start.date()} to {period_end.date()}")

        # 2. Regulation Fetcher Agent (RAG)
        regulations_result = await fetch_regulations_agent(domain, entity_type)
        if not regulations_result["success"]:
            return PipelineRunResponse(success=False, error=regulations_result["error"])
        regulations = regulations_result["regulations"]
        await asyncio.sleep(5)  # Delay to avoid rate limiting

        # 3. Compliance Validator Agent
        compliance_result = await validate_batch_transactions_agent(transactions, domain, entity_type)
        if not compliance_result["success"]:
            return PipelineRunResponse(success=False, error=compliance_result["error"])
        compliance_summary = compliance_result["summary"]
        flagged_entries = [r for r in compliance_result["validation_results"] if r["validation_result"]["status"] == "INVALID"]
        await asyncio.sleep(5)  # Delay to avoid rate limiting

        # 4. Filing Data Aggregator Agent
        filing_result = await generate_filing_ready_data_agent(filing_type, transactions, period_start, period_end)
        if not filing_result["success"]:
            return PipelineRunResponse(success=False, error=filing_result["error"])
        filing_summary = filing_result["summary"]
        await asyncio.sleep(5)  # Delay to avoid rate limiting

        # 5. Anomaly Detector Agent
        anomaly_result = await detect_anomalies_agent(transactions)
        if not anomaly_result["success"]:
            return PipelineRunResponse(success=False, error=anomaly_result["error"])
        anomalies = anomaly_result["anomalies"]
        await asyncio.sleep(5)  # Delay to avoid rate limiting

        # 6. Filing Report Generator Agent
        report_result = await generate_filing_report_agent(filing_type, period_start, period_end)
        if not report_result["success"]:
            return PipelineRunResponse(success=False, error=report_result["error"])

        # Dashboard summary
        dashboard = {
            "compliance_summary": compliance_summary,
            "flagged_entries": flagged_entries,
            "filing_summary": filing_summary,
            "anomalies": anomalies,
            "report": report_result
        }

        return PipelineRunResponse(
            success=True,
            compliance_summary=compliance_summary,
            flagged_entries=flagged_entries,
            filing_summary=filing_summary,
            anomalies=anomalies,
            report=report_result,
            dashboard=dashboard
        )
    except Exception as e:
        logger.error(f"Error running pipeline: {e}")
        return PipelineRunResponse(success=False, error=str(e)) 