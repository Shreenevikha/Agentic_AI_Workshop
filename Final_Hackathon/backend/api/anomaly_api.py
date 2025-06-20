"""
Anomaly Detector API
API endpoints for anomaly detection functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from agents.anomaly_detector_agent import (
    detect_anomalies_agent,
    get_anomaly_summary_agent,
    resolve_anomaly_agent
)
from models.mongo_models import FinancialTransaction
from database.mongo_database import connect_to_mongo
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/anomalies", tags=["anomalies"])

# Pydantic models
class AnomalyDetectionRequest(BaseModel):
    transaction_ids: Optional[List[str]] = None

class AnomalyDetectionResponse(BaseModel):
    success: bool
    anomalies: Optional[List[Dict[str, Any]]] = None
    anomaly_summary: Optional[Dict[str, Any]] = None
    count: Optional[int] = None
    execution_id: str
    error: Optional[str] = None

class AnomalySummaryResponse(BaseModel):
    success: bool
    anomaly_summary: Optional[Dict[str, Any]] = None
    anomalies: Optional[List[Dict[str, Any]]] = None
    execution_id: str
    error: Optional[str] = None

class ResolveAnomalyRequest(BaseModel):
    resolution_action: str

class ResolveAnomalyResponse(BaseModel):
    success: bool
    anomaly_id: Optional[str] = None
    status: Optional[str] = None
    execution_id: str
    error: Optional[str] = None

@router.post("/detect", response_model=AnomalyDetectionResponse)
async def detect_anomalies(request: AnomalyDetectionRequest):
    """Detect anomalies in transaction data"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Get transactions
        query = {}
        if request.transaction_ids:
            query["transaction_id"] = {"$in": request.transaction_ids}
        
        transactions = await FinancialTransaction.find(query).to_list()
        
        if not transactions:
            return AnomalyDetectionResponse(
                success=True,
                anomalies=[],
                anomaly_summary={"total": 0, "by_type": {}, "by_severity": {}, "quick_fixes": []},
                count=0,
                execution_id="no-transactions"
            )
        
        # Detect anomalies
        result = await detect_anomalies_agent(transactions)
        
        if result["success"]:
            return AnomalyDetectionResponse(
                success=True,
                anomalies=result["anomalies"],
                anomaly_summary=result["anomaly_summary"],
                count=result["count"],
                execution_id=result["execution_id"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary", response_model=AnomalySummaryResponse)
async def get_anomaly_summary():
    """Get summary of all anomalies"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Get anomaly summary
        result = await get_anomaly_summary_agent()
        
        if result["success"]:
            return AnomalySummaryResponse(
                success=True,
                anomaly_summary=result["anomaly_summary"],
                anomalies=result["anomalies"],
                execution_id=result["execution_id"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error getting anomaly summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{anomaly_id}/resolve", response_model=ResolveAnomalyResponse)
async def resolve_anomaly(anomaly_id: str, request: ResolveAnomalyRequest):
    """Resolve an anomaly"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Resolve anomaly
        result = await resolve_anomaly_agent(anomaly_id, request.resolution_action)
        
        if result["success"]:
            return ResolveAnomalyResponse(
                success=True,
                anomaly_id=result["anomaly_id"],
                status=result["status"],
                execution_id=result["execution_id"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error resolving anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types")
async def get_anomaly_types():
    """Get list of anomaly types and their descriptions"""
    try:
        return {
            "success": True,
            "anomaly_types": [
                {
                    "type": "DUPLICATE",
                    "description": "Duplicate transactions found",
                    "severity": "MEDIUM",
                    "common_causes": ["Data import errors", "System glitches", "Manual entry mistakes"]
                },
                {
                    "type": "MISMATCH",
                    "description": "Data format or validation mismatches",
                    "severity": "HIGH",
                    "common_causes": ["Invalid GSTIN", "Missing PAN", "Incorrect tax rates"]
                },
                {
                    "type": "SUSPICIOUS",
                    "description": "Suspicious or unusual patterns",
                    "severity": "MEDIUM",
                    "common_causes": ["Unusually high amounts", "Future dates", "Very old transactions"]
                }
            ],
            "severity_levels": [
                {
                    "level": "LOW",
                    "description": "Minor issues that don't affect filing",
                    "action": "Review and monitor"
                },
                {
                    "level": "MEDIUM",
                    "description": "Issues that may affect filing accuracy",
                    "action": "Review and fix before filing"
                },
                {
                    "level": "HIGH",
                    "description": "Critical issues that must be fixed",
                    "action": "Fix immediately before filing"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting anomaly types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quick-fixes")
async def get_quick_fixes():
    """Get common quick fixes for anomalies"""
    try:
        return {
            "success": True,
            "quick_fixes": [
                {
                    "anomaly_type": "DUPLICATE",
                    "fix": "Review and remove duplicate entries. Keep only one transaction if they are truly duplicates.",
                    "steps": [
                        "Identify duplicate transactions",
                        "Verify if they are actual duplicates",
                        "Remove or merge duplicate entries",
                        "Update transaction records"
                    ]
                },
                {
                    "anomaly_type": "MISMATCH",
                    "fix": "Correct data format and validation issues.",
                    "steps": [
                        "Verify GSTIN format (15 characters)",
                        "Add missing PAN numbers",
                        "Correct tax rate calculations",
                        "Validate invoice formats"
                    ]
                },
                {
                    "anomaly_type": "SUSPICIOUS",
                    "fix": "Review and verify unusual patterns.",
                    "steps": [
                        "Verify transaction amounts",
                        "Correct transaction dates",
                        "Review old transactions",
                        "Document legitimate large transactions"
                    ]
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting quick fixes: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 