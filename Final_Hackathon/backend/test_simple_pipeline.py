#!/usr/bin/env python3
"""
Simple test script to identify pipeline issues
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.mongo_database import connect_to_mongo
from models.mongo_models import FinancialTransaction
from agents.regulation_fetcher_agent import fetch_regulations_agent
from agents.compliance_validator_agent import validate_batch_transactions_agent
from agents.filing_data_aggregator_agent import generate_filing_ready_data_agent
from agents.anomaly_detector_agent import detect_anomalies_agent
from agents.filing_report_generator_agent import generate_filing_report_agent

async def test_pipeline():
    """Test each agent individually to identify the issue"""
    
    # Initialize database connection
    print("Initializing database connection...")
    try:
        await connect_to_mongo()
        print("✅ Database connection initialized")
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
        print("Continuing with in-memory mode...")
    
    # Create sample transaction
    transaction = FinancialTransaction(
        transaction_id="TEST-001",
        date=datetime(2024, 1, 15),
        amount=1000.0,
        description="Test transaction",
        category="Test",
        tax_type="GST",
        compliance_status="pending",
        validation_notes=""
    )
    
    transactions = [transaction]
    
    print("Testing individual agents...")
    
    # Test 1: Regulation Fetcher
    print("\n1. Testing Regulation Fetcher Agent...")
    try:
        result = await fetch_regulations_agent("tax", "business")
        print(f"✅ Regulation Fetcher: {result['success']}")
        if not result['success']:
            print(f"   Error: {result['error']}")
    except Exception as e:
        print(f"❌ Regulation Fetcher failed: {e}")
    
    # Test 2: Compliance Validator
    print("\n2. Testing Compliance Validator Agent...")
    try:
        result = await validate_batch_transactions_agent(transactions, "tax", "business")
        print(f"✅ Compliance Validator: {result['success']}")
        if not result['success']:
            print(f"   Error: {result['error']}")
    except Exception as e:
        print(f"❌ Compliance Validator failed: {e}")
    
    # Test 3: Filing Data Aggregator
    print("\n3. Testing Filing Data Aggregator Agent...")
    try:
        result = await generate_filing_ready_data_agent("GSTR-1", transactions, datetime(2024, 1, 1), datetime(2024, 1, 31))
        print(f"✅ Filing Data Aggregator: {result['success']}")
        if not result['success']:
            print(f"   Error: {result['error']}")
    except Exception as e:
        print(f"❌ Filing Data Aggregator failed: {e}")
    
    # Test 4: Anomaly Detector
    print("\n4. Testing Anomaly Detector Agent...")
    try:
        result = await detect_anomalies_agent(transactions)
        print(f"✅ Anomaly Detector: {result['success']}")
        if not result['success']:
            print(f"   Error: {result['error']}")
    except Exception as e:
        print(f"❌ Anomaly Detector failed: {e}")
    
    # Test 5: Report Generator
    print("\n5. Testing Report Generator Agent...")
    try:
        result = await generate_filing_report_agent("GSTR-1", datetime(2024, 1, 1), datetime(2024, 1, 31))
        print(f"✅ Report Generator: {result['success']}")
        if not result['success']:
            print(f"   Error: {result['error']}")
    except Exception as e:
        print(f"❌ Report Generator failed: {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_pipeline()) 