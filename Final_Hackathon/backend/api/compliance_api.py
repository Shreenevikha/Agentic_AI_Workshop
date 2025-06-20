"""
Compliance Validator API
API endpoints for compliance validation functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from agents.compliance_validator_agent import (
    initialize_compliance_validator_agent,
    validate_batch_transactions_agent,
    flag_invalid_entries_agent
)
from models.mongo_models import FinancialTransaction
from database.mongo_database import connect_to_mongo
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])

# Pydantic models
class ValidationRequest(BaseModel):
    domain: str
    entity_type: str
    transaction_ids: Optional[List[str]] = None

class ValidationResponse(BaseModel):
    success: bool
    validation_results: Optional[List[Dict[str, Any]]] = None
    summary: Optional[Dict[str, Any]] = None
    execution_id: str
    error: Optional[str] = None

class FlaggedEntriesResponse(BaseModel):
    success: bool
    flagged_entries: Optional[List[Dict[str, Any]]] = None
    count: Optional[int] = None
    execution_id: str
    error: Optional[str] = None

@router.post("/validate", response_model=ValidationResponse)
async def validate_transactions(request: ValidationRequest):
    """Validate transactions against regulations"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Get transactions
        query = {}
        if request.transaction_ids:
            query["transaction_id"] = {"$in": request.transaction_ids}
        
        transactions = await FinancialTransaction.find(query).to_list()
        
        if not transactions:
            return ValidationResponse(
                success=True,
                validation_results=[],
                summary={"total": 0, "valid": 0, "invalid": 0, "pending": 0},
                execution_id="no-transactions"
            )
        
        # Validate transactions
        result = await validate_batch_transactions_agent(
            transactions, request.domain, request.entity_type
        )
        
        if result["success"]:
            return ValidationResponse(
                success=True,
                validation_results=result["validation_results"],
                summary=result["summary"],
                execution_id=result["execution_id"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error validating transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/flagged-entries", response_model=FlaggedEntriesResponse)
async def get_flagged_entries():
    """Get all flagged invalid entries"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Get invalid transactions
        invalid_transactions = await FinancialTransaction.find({
            "compliance_status": "INVALID"
        }).to_list()
        
        # Flag invalid entries
        result = await flag_invalid_entries_agent(invalid_transactions)
        
        if result["success"]:
            return FlaggedEntriesResponse(
                success=True,
                flagged_entries=result["flagged_entries"],
                count=result["count"],
                execution_id=result["execution_id"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error getting flagged entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validation-summary")
async def get_validation_summary():
    """Get summary of validation status"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Get validation summary
        total = await FinancialTransaction.count()
        valid = await FinancialTransaction.count({"compliance_status": "VALID"})
        invalid = await FinancialTransaction.count({"compliance_status": "INVALID"})
        pending = await FinancialTransaction.count({"compliance_status": "PENDING"})
        
        return {
            "success": True,
            "summary": {
                "total": total,
                "valid": valid,
                "invalid": invalid,
                "pending": pending,
                "compliance_rate": (valid / total * 100) if total > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting validation summary: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 