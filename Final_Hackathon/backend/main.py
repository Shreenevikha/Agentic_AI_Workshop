from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn
import asyncio
from core.config import settings
from database.mongo_database import connect_to_mongo, close_mongo_connection, MongoDB
from api.regulation_api import router as regulation_router
from api.rag_api import router as rag_router
from api.compliance_api import router as compliance_router
from api.filing_api import router as filing_router
from api.anomaly_api import router as anomaly_router
from api.report_api import router as report_router
from api.pipeline_api import router as pipeline_router
from agents.regulation_fetcher_agent import initialize_regulation_fetcher_agent
from agents.compliance_validator_agent import initialize_compliance_validator_agent
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Tax Compliance AI Assistant",
    description="Agentic AI-Based Autonomous Compliance Checker & Tax Filing Assistant with Full RAG Pipeline and 5-Agent System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize database connection and agents on startup"""
    try:
        await connect_to_mongo()
        if MongoDB.is_connected:
            logger.info("Connected to MongoDB")
        else:
            logger.warning("MongoDB not available - running in development mode")
        
        # Initialize regulation fetcher agent and vector store with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                success = initialize_regulation_fetcher_agent()
                if success:
                    logger.info("Regulation Fetcher Agent and Vector Store initialized successfully")
                    break
                else:
                    logger.warning(f"Attempt {attempt + 1}/{max_retries}: Failed to initialize Regulation Fetcher Agent")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)  # Wait before retry
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries}: Exception during Regulation Fetcher initialization: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)  # Wait before retry
        
        if not success:
            logger.error("Failed to initialize Regulation Fetcher Agent after all retries")
        
        # Initialize compliance validator agent
        compliance_success = initialize_compliance_validator_agent()
        if compliance_success:
            logger.info("Compliance Validator Agent initialized successfully")
        else:
            logger.warning("Failed to initialize Compliance Validator Agent - will initialize when needed")
        
        logger.info("Application started successfully with 5-Agent System")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        # Don't raise the exception, just log it and continue

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    try:
        await close_mongo_connection()
        logger.info("Application shutdown successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Tax Compliance AI Assistant with Full RAG Pipeline",
        "version": "1.0.0"
    }

# Test endpoint for proxy
@app.get("/test-proxy")
async def test_proxy():
    """Test endpoint for proxy verification"""
    return {
        "message": "Proxy is working!",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success"
    }

# Include routers
app.include_router(regulation_router)
app.include_router(rag_router)
app.include_router(compliance_router)
app.include_router(filing_router)
app.include_router(anomaly_router)
app.include_router(report_router)
app.include_router(pipeline_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Tax Compliance AI Assistant with Full RAG Pipeline",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "features": [
            "Regulation Fetcher Agent",
            "RAG Compliance Query Agent", 
            "Hybrid Search Agent",
            "Vector Database (ChromaDB)",
            "MongoDB Integration",
            "Gemini AI Integration",
            "Compliance Validator Agent"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 