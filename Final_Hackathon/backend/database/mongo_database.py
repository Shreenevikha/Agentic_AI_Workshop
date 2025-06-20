from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from core.config import settings
import logging
from models.mongo_models import (
    Regulation, FinancialTransaction, ComplianceValidation,
    Anomaly, FilingReport, AgentExecutionLog
)

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    is_connected: bool = False

async def connect_to_mongo():
    """Create database connection"""
    try:
        MongoDB.client = AsyncIOMotorClient(settings.mongodb_url)
        # Test the connection
        await MongoDB.client.admin.command('ping')
        MongoDB.is_connected = True
        logger.info("Connected to MongoDB")
        
        # Initialize Beanie with all document models
        await init_beanie(
            database=MongoDB.client.tax_compliance,
            document_models=[
                Regulation,
                FinancialTransaction,
                ComplianceValidation,
                Anomaly,
                FilingReport,
                AgentExecutionLog
            ]
        )
        logger.info("Beanie initialized successfully")
        
    except Exception as e:
        logger.warning(f"Failed to connect to MongoDB: {e}")
        logger.info("Running in development mode without database - some features may be limited")
        MongoDB.is_connected = False
        # Don't raise the exception, just log it

async def close_mongo_connection():
    """Close database connection"""
    try:
        if MongoDB.client and MongoDB.is_connected:
            MongoDB.client.close()
            MongoDB.is_connected = False
            logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")

def get_database():
    """Get database instance"""
    if MongoDB.client and MongoDB.is_connected:
        return MongoDB.client.tax_compliance
    else:
        logger.warning("Database not connected - returning None")
        return None 