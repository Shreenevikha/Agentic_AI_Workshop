from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from agents.regulation_fetcher_agent import (
    initialize_regulation_fetcher_agent,
    fetch_regulations_agent,
    sync_regulations_agent,
    search_vector_store_agent
)
from database.mongo_database import connect_to_mongo
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/regulations", tags=["regulations"])

# Pydantic models for request/response
class FetchRegulationsRequest(BaseModel):
    domain: str
    entity_type: str

class RegulationData(BaseModel):
    title: str
    content: str
    domain: str
    entity_type: str
    source_url: Optional[str] = None
    effective_date: Optional[str] = None
    version: Optional[str] = "1.0"

class SyncRegulationsRequest(BaseModel):
    regulations: List[RegulationData]

class RegulationResponse(BaseModel):
    success: bool
    regulations: Optional[List[Dict[str, Any]]] = None
    count: Optional[int] = None
    execution_id: str
    error: Optional[str] = None

class SyncResponse(BaseModel):
    success: bool
    synced_count: Optional[int] = None
    execution_id: str
    error: Optional[str] = None

# Initialize agent on startup
@router.on_event("startup")
async def startup_event():
    """Initialize the regulation fetcher agent on startup"""
    try:
        success = initialize_regulation_fetcher_agent()
        if success:
            logger.info("Regulation Fetcher Agent initialized successfully")
        else:
            logger.error("Failed to initialize Regulation Fetcher Agent")
    except Exception as e:
        logger.error(f"Error initializing agent: {e}")

@router.post("/fetch", response_model=RegulationResponse)
async def fetch_regulations(request: FetchRegulationsRequest):
    """Fetch regulations for a specific domain and entity type"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        result = await fetch_regulations_agent(
            domain=request.domain,
            entity_type=request.entity_type
        )
        
        if result["success"]:
            return RegulationResponse(
                success=True,
                regulations=result["regulations"],
                count=result["count"],
                execution_id=result["execution_id"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error fetching regulations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync", response_model=SyncResponse)
async def sync_regulations(request: SyncRegulationsRequest):
    """Sync regulations from external sources"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Convert Pydantic models to dictionaries
        regulation_data = []
        for reg in request.regulations:
            reg_dict = reg.dict()
            if reg.effective_date:
                reg_dict["effective_date"] = reg.effective_date
            regulation_data.append(reg_dict)
        
        result = await sync_regulations_agent(regulation_data)
        
        if result["success"]:
            return SyncResponse(
                success=True,
                synced_count=result["regulations_synced"],
                execution_id=result["execution_id"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error syncing regulations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_regulations(
    query: str,
    domain: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = 10
):
    """Search regulations using vector similarity"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Use the agent's vector search capability
        if domain and entity_type:
            results = await search_vector_store_agent(domain, entity_type)
        else:
            # Generic search - this would need to be implemented
            results = []
        
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching regulations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/domains")
async def get_available_domains():
    """Get list of available regulation domains"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        from models.mongo_models import Regulation
        
        # Get unique domains from database
        domains = await Regulation.distinct("domain")
        
        return {
            "success": True,
            "domains": domains
        }
        
    except Exception as e:
        logger.error(f"Error getting domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entity-types")
async def get_available_entity_types(domain: Optional[str] = None):
    """Get list of available entity types"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        from models.mongo_models import Regulation
        
        # Build query
        query = {}
        if domain:
            query["domain"] = domain
        
        # Get unique entity types
        entity_types = await Regulation.distinct("entity_type", query)
        
        return {
            "success": True,
            "entity_types": entity_types
        }
        
    except Exception as e:
        logger.error(f"Error getting entity types: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 