"""
Filing Data Aggregator API
API endpoints for filing data aggregation functionality
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from agents.filing_data_aggregator_agent import (
    generate_filing_ready_data_agent,
    get_filing_readiness_summary_agent
)
from models.mongo_models import FinancialTransaction
from database.mongo_database import connect_to_mongo, MongoDB
import logging
import pandas as pd
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/filing", tags=["filing"])

# In-memory storage for development when MongoDB is not available
in_memory_transactions = []

# Pydantic models
class FilingRequest(BaseModel):
    filing_type: str
    period_start: datetime
    period_end: datetime

class FilingResponse(BaseModel):
    success: bool
    filing_type: Optional[str] = None
    readiness_level: Optional[float] = None
    government_schema_json: Optional[str] = None
    csv_data: Optional[str] = None
    report_id: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    execution_id: str
    error: Optional[str] = None

class ReadinessSummaryResponse(BaseModel):
    success: bool
    readiness_summary: Optional[Dict[str, Any]] = None
    period: Optional[str] = None
    execution_id: str
    error: Optional[str] = None

class UploadResponse(BaseModel):
    success: bool
    message: str
    total_transactions: int
    transactions_saved: int
    errors: List[str] = []

@router.post("/upload", response_model=UploadResponse)
async def upload_transactions(file: UploadFile = File(...)):
    """Upload and process a CSV file of financial transactions"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    try:
        await connect_to_mongo()
        
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Basic validation
        required_columns = {'date', 'description', 'amount'}
        if not required_columns.issubset(df.columns):
            raise HTTPException(status_code=400, detail=f"CSV must contain columns: {', '.join(required_columns)}")

        transactions_to_save = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Data cleaning and validation
                transaction_data = {
                    "transaction_id": str(hash(f"{row.get('date', '')}{row.get('description', '')}{row.get('amount', '')}{index}")),
                    "date": pd.to_datetime(row['date']).replace(tzinfo=timezone.utc),
                    "description": str(row['description']),
                    "amount": float(row['amount']),
                    "category": row.get('category', ''),
                    "vendor": row.get('vendor', ''),
                    "is_debit": bool(row.get('is_debit', True)),
                    "tags": row.get('tags', []),
                    "compliance_status": "pending",
                    "validation_notes": ""
                }
                
                transaction = FinancialTransaction(**transaction_data)
                transactions_to_save.append(transaction)
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")

        # Save transactions based on database availability
        if MongoDB.is_connected and transactions_to_save:
            await FinancialTransaction.insert_many(transactions_to_save)
            logger.info(f"Saved {len(transactions_to_save)} transactions to MongoDB")
        else:
            # Store in memory for development
            global in_memory_transactions
            in_memory_transactions.extend(transactions_to_save)
            logger.info(f"Stored {len(transactions_to_save)} transactions in memory (MongoDB not available)")

        return UploadResponse(
            success=True,
            message=f"Successfully processed file: {file.filename}",
            total_transactions=len(df),
            transactions_saved=len(transactions_to_save),
            errors=errors
        )

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions directly to preserve status code and detail
        raise http_exc
    except Exception as e:
        # For all other exceptions, return a detailed error message
        error_message = f"An unexpected error occurred: {type(e).__name__} - {e}"
        logger.error(f"Error processing upload: {error_message}")
        raise HTTPException(status_code=500, detail=error_message)

@router.post("/generate", response_model=FilingResponse)
async def generate_filing_data(request: FilingRequest):
    """Generate filing-ready data for specified type and period"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Get transactions for the period
        transactions = await FinancialTransaction.find({
            "date": {"$gte": request.period_start, "$lte": request.period_end}
        }).to_list()
        
        # Generate filing data
        result = await generate_filing_ready_data_agent(
            request.filing_type, transactions, request.period_start, request.period_end
        )
        
        if result["success"]:
            return FilingResponse(
                success=True,
                filing_type=result["filing_type"],
                readiness_level=result["readiness_level"],
                government_schema_json=result["government_schema_json"],
                csv_data=result["csv_data"],
                report_id=result["report_id"],
                summary=result["summary"],
                execution_id=result["execution_id"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error generating filing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/readiness-summary", response_model=ReadinessSummaryResponse)
async def get_filing_readiness_summary():
    """Get summary of all filing readiness levels"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Get readiness summary
        result = await get_filing_readiness_summary_agent()
        
        if result["success"]:
            return ReadinessSummaryResponse(
                success=True,
                readiness_summary=result["readiness_summary"],
                period=result["period"],
                execution_id=result["execution_id"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error getting filing readiness summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/filing-types")
async def get_supported_filing_types():
    """Get list of supported filing types"""
    try:
        return {
            "success": True,
            "filing_types": [
                {
                    "type": "GSTR-1",
                    "description": "Outward supplies return",
                    "frequency": "monthly",
                    "due_date": "11th of next month"
                },
                {
                    "type": "GSTR-3B",
                    "description": "Summary return",
                    "frequency": "monthly",
                    "due_date": "20th of next month"
                },
                {
                    "type": "TDS-26Q",
                    "description": "TDS on salaries",
                    "frequency": "quarterly",
                    "due_date": "31st of next month after quarter"
                },
                {
                    "type": "TDS-24Q",
                    "description": "TDS on non-salaries",
                    "frequency": "quarterly",
                    "due_date": "31st of next month after quarter"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting filing types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/periods")
async def get_filing_periods():
    """Get available filing periods"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Get unique periods from transactions
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$date"},
                        "month": {"$month": "$date"}
                    }
                }
            },
            {"$sort": {"_id.year": -1, "_id.month": -1}}
        ]
        
        periods = await FinancialTransaction.aggregate(pipeline).to_list()
        
        formatted_periods = []
        for period in periods:
            year = period["_id"]["year"]
            month = period["_id"]["month"]
            formatted_periods.append({
                "year": year,
                "month": month,
                "label": f"{year}-{month:02d}",
                "start_date": f"{year}-{month:02d}-01",
                "end_date": f"{year}-{month:02d}-31"
            })
        
        return {
            "success": True,
            "periods": formatted_periods
        }
        
    except Exception as e:
        logger.error(f"Error getting filing periods: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 