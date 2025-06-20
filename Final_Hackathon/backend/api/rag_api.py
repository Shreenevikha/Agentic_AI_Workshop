from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from agents.rag_agent import (
    initialize_rag_agent,
    rag_compliance_query_agent,
    hybrid_search_agent
)
from agents.regulation_fetcher_agent import vector_store
from database.mongo_database import connect_to_mongo
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])

# Pydantic models for request/response
class RAGQueryRequest(BaseModel):
    query: str
    domain: Optional[str] = None
    entity_type: Optional[str] = None

class HybridSearchRequest(BaseModel):
    query: str
    domain: Optional[str] = None
    entity_type: Optional[str] = None
    limit: Optional[int] = 10

class RAGResponse(BaseModel):
    success: bool
    answer: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    execution_id: str
    error: Optional[str] = None

class HybridSearchResponse(BaseModel):
    success: bool
    results: Optional[List[Dict[str, Any]]] = None
    count: Optional[int] = None
    execution_id: str
    error: Optional[str] = None

# Initialize RAG agent on startup
@router.on_event("startup")
async def startup_event():
    """Initialize the RAG agent on startup"""
    try:
        if vector_store:
            success = initialize_rag_agent(vector_store)
            if success:
                logger.info("RAG Agent initialized successfully")
            else:
                logger.error("Failed to initialize RAG Agent")
        else:
            logger.warning("Vector store not available for RAG agent initialization - will initialize when needed")
    except Exception as e:
        logger.error(f"Error initializing RAG agent: {e}")

@router.post("/query", response_model=RAGResponse)
async def rag_compliance_query(request: RAGQueryRequest):
    """Query tax compliance using RAG pipeline"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        # Try to initialize RAG agent if not already done
        if not vector_store:
            raise HTTPException(
                status_code=503, 
                detail="Vector store not available. Please ensure regulation fetcher agent is initialized first."
            )
        
        result = await rag_compliance_query_agent(
            query=request.query,
            domain=request.domain,
            entity_type=request.entity_type
        )
        
        if result["success"]:
            return RAGResponse(
                success=True,
                answer=result["answer"],
                sources=result["sources"],
                execution_id=result["execution_id"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in RAG query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hybrid-search", response_model=HybridSearchResponse)
async def hybrid_search(request: HybridSearchRequest):
    """Perform hybrid search combining vector and keyword search"""
    try:
        # Ensure database connection
        await connect_to_mongo()
        
        if not vector_store:
            raise HTTPException(
                status_code=503, 
                detail="Vector store not available. Please ensure regulation fetcher agent is initialized first."
            )
        
        result = await hybrid_search_agent(
            query=request.query,
            vector_store=vector_store,
            domain=request.domain,
            entity_type=request.entity_type
        )
        
        if result["success"]:
            return HybridSearchResponse(
                success=True,
                results=result["results"],
                count=result["count"],
                execution_id=result["execution_id"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in hybrid search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def rag_health_check():
    """Health check for RAG components"""
    try:
        # Check if vector store is available
        vector_store_status = "available" if vector_store else "unavailable"
        
        # Try to get RAG agent status
        from agents.rag_agent import is_initialized
        rag_status = "initialized" if is_initialized else "not_initialized"
        
        return {
            "status": "healthy" if vector_store else "degraded",
            "vector_store": vector_store_status,
            "rag_agent": rag_status,
            "message": "RAG system is ready" if vector_store and is_initialized else "RAG system needs initialization"
        }
        
    except Exception as e:
        logger.error(f"Error in RAG health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capabilities")
async def get_rag_capabilities():
    """Get RAG system capabilities"""
    return {
        "capabilities": [
            "Retrieval-Augmented Generation (RAG)",
            "Contextual Compression",
            "Hybrid Search (Vector + Keyword)",
            "Source Document Retrieval",
            "Tax Compliance Query Processing",
            "Multi-domain Support (GST, TDS, VAT, etc.)",
            "Entity Type Filtering"
        ],
        "models": {
            "llm": "Google Gemini Pro",
            "embeddings": "HuggingFace Sentence Transformers",
            "vector_store": "ChromaDB",
            "database": "MongoDB with Beanie ODM"
        },
        "features": {
            "contextual_compression": True,
            "source_tracking": True,
            "execution_logging": True,
            "hybrid_search": True
        }
    }

@router.post("/initialize")
async def initialize_rag_system():
    """Manually initialize RAG system"""
    try:
        if not vector_store:
            raise HTTPException(
                status_code=503, 
                detail="Vector store not available. Please initialize regulation fetcher agent first."
            )
        
        success = initialize_rag_agent(vector_store)
        if success:
            return {"success": True, "message": "RAG system initialized successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to initialize RAG system")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing RAG system: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 