#!/usr/bin/env python3
"""
Quick test script for Regulation Fetcher Agent
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.mongo_database import connect_to_mongo
from agents.regulation_fetcher_agent import initialize_regulation_fetcher_agent, sync_regulations_agent, fetch_regulations_agent

async def test_regulation_fetcher():
    """Test regulation fetcher initialization and sync"""
    
    print("🔧 Testing Regulation Fetcher Agent...")
    
    # Initialize database
    print("1. Initializing database...")
    try:
        await connect_to_mongo()
        print("✅ Database connected")
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
    
    # Test initialization
    print("\n2. Testing agent initialization...")
    success = initialize_regulation_fetcher_agent()
    if success:
        print("✅ Regulation Fetcher Agent initialized successfully")
    else:
        print("❌ Failed to initialize Regulation Fetcher Agent")
        return
    
    # Test sync with sample data
    print("\n3. Testing regulation sync...")
    sample_regulations = [
        {
            "title": "GST Registration Requirements",
            "content": "Businesses with turnover exceeding Rs. 20 lakhs must register for GST. Registration is mandatory for interstate supplies regardless of turnover.",
            "domain": "tax",
            "entity_type": "business",
            "source_url": "https://gst.gov.in",
            "effective_date": datetime(2023, 1, 1),
            "expiry_date": None,
            "version": "1.0",
            "vector_id": "gst_reg_001"
        },
        {
            "title": "TDS Compliance Rules",
            "content": "TDS must be deducted at source for payments exceeding specified thresholds. Rate varies by payment type and recipient category.",
            "domain": "tax", 
            "entity_type": "business",
            "source_url": "https://incometax.gov.in",
            "effective_date": datetime(2023, 1, 1),
            "expiry_date": None,
            "version": "1.0",
            "vector_id": "tds_comp_001"
        }
    ]
    
    try:
        result = await sync_regulations_agent(sample_regulations)
        if result["success"]:
            print(f"✅ Synced {result['regulations_synced']} regulations successfully")
            if result["errors"]:
                print(f"⚠️ {len(result['errors'])} errors occurred")
        else:
            print(f"❌ Sync failed: {result['error']}")
    except Exception as e:
        print(f"❌ Sync exception: {e}")
    
    # Test fetch regulations
    print("\n4. Testing regulation fetch...")
    try:
        result = await fetch_regulations_agent("tax", "business")
        if result["success"]:
            print(f"✅ Fetched {result['count']} regulations successfully")
        else:
            print(f"❌ Fetch failed: {result['error']}")
    except Exception as e:
        print(f"❌ Fetch exception: {e}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_regulation_fetcher()) 