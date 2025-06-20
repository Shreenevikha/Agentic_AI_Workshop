#!/usr/bin/env python3
"""
Test script for pipeline upload functionality
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.mongo_database import connect_to_mongo
from api.pipeline_api import run_pipeline
from fastapi import UploadFile
import io

async def test_pipeline_upload():
    """Test the pipeline upload functionality"""
    
    print("🔧 Testing Pipeline Upload...")
    
    # Initialize database
    print("1. Initializing database...")
    try:
        await connect_to_mongo()
        print("✅ Database connected")
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
    
    # Create sample CSV content
    csv_content = """date,description,amount,category,vendor,tax_type,is_debit
2024-01-15,Office Supplies Purchase,1250.00,Office Expenses,OfficeMax,GST,True
2024-01-20,Client Payment Received,50000.00,Revenue,Client ABC,Income Tax,False
2024-01-25,Internet Service Bill,2500.00,Utilities,Internet Provider,GST,True
2024-02-01,Employee Salary,35000.00,Payroll,Employee XYZ,TDS,True
2024-02-05,Software License,15000.00,Technology,Software Corp,GST,True"""
    
    # Create a mock UploadFile
    file_content = io.BytesIO(csv_content.encode('utf-8'))
    mock_file = UploadFile(
        filename="test_transactions.csv",
        file=file_content
    )
    
    print("2. Testing pipeline execution...")
    try:
        # Test the pipeline
        result = await run_pipeline(
            domain="tax",
            entity_type="business", 
            filing_type="GSTR-1",
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 2, 29),
            file=mock_file
        )
        
        if result.success:
            print("✅ Pipeline executed successfully!")
            print(f"   - Compliance Summary: {result.compliance_summary}")
            print(f"   - Flagged Entries: {len(result.flagged_entries or [])}")
            print(f"   - Filing Summary: {result.filing_summary}")
            print(f"   - Anomalies: {len(result.anomalies or [])}")
        else:
            print(f"❌ Pipeline failed: {result.error}")
            
    except Exception as e:
        print(f"❌ Pipeline exception: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_pipeline_upload()) 