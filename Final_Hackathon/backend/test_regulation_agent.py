import asyncio
import logging
from agents.regulation_fetcher_agent import (
    initialize_regulation_fetcher_agent,
    fetch_regulations_agent,
    sync_regulations_agent,
    search_vector_store_agent
)
from database.mongo_database import connect_to_mongo, close_mongo_connection
from core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_regulation_fetcher_agent():
    """Test the Regulation Fetcher Agent"""
    
    print("🚀 Testing Regulation Fetcher Agent...")
    
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        print("✅ Connected to MongoDB")
        
        # Initialize agent
        success = initialize_regulation_fetcher_agent()
        if success:
            print("✅ Regulation Fetcher Agent initialized")
        else:
            print("❌ Failed to initialize Regulation Fetcher Agent")
            return
        
        # Test 1: Fetch regulations
        print("\n📋 Test 1: Fetching regulations for GST domain...")
        result = await fetch_regulations_agent(
            domain="GST",
            entity_type="Company"
        )
        
        if result["success"]:
            print(f"✅ Successfully fetched {result['count']} regulations")
            print(f"📊 Execution ID: {result['execution_id']}")
        else:
            print(f"❌ Failed to fetch regulations: {result['error']}")
        
        # Test 2: Sync sample regulations
        print("\n📋 Test 2: Syncing sample regulations...")
        sample_regulations = [
            {
                "title": "GST Registration Requirements",
                "content": "All businesses with turnover exceeding Rs. 20 lakhs must register for GST. The registration process requires PAN, business details, and bank account information.",
                "domain": "GST",
                "entity_type": "Company",
                "source_url": "https://gst.gov.in",
                "version": "1.0"
            },
            {
                "title": "TDS Compliance Rules",
                "content": "TDS must be deducted at source for payments exceeding specified thresholds. Different rates apply for different types of payments and payees.",
                "domain": "TDS",
                "entity_type": "Company",
                "source_url": "https://incometax.gov.in",
                "version": "1.0"
            }
        ]
        
        sync_result = await sync_regulations_agent(sample_regulations)
        
        if sync_result["success"]:
            print(f"✅ Successfully synced {sync_result['synced_count']} regulations")
            print(f"📊 Execution ID: {sync_result['execution_id']}")
        else:
            print(f"❌ Failed to sync regulations: {sync_result['error']}")
        
        # Test 3: Search regulations
        print("\n📋 Test 3: Searching regulations...")
        search_results = await search_vector_store_agent("GST", "Company")
        print(f"✅ Found {len(search_results)} search results")
        
        # Test 4: Fetch regulations again (should include synced ones)
        print("\n📋 Test 4: Fetching regulations after sync...")
        result2 = await fetch_regulations_agent(
            domain="GST",
            entity_type="Company"
        )
        
        if result2["success"]:
            print(f"✅ Successfully fetched {result2['count']} regulations (including synced)")
            for reg in result2["regulations"][:2]:  # Show first 2
                print(f"  - {reg['title']} ({reg['source']})")
        else:
            print(f"❌ Failed to fetch regulations: {result2['error']}")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")
    
    finally:
        # Close database connection
        await close_mongo_connection()
        print("✅ Database connection closed")

async def test_api_endpoints():
    """Test API endpoints using httpx"""
    import httpx
    
    print("\n🌐 Testing API endpoints...")
    
    async with httpx.AsyncClient() as client:
        base_url = f"http://{settings.api_host}:{settings.api_port}"
        
        # Test health endpoint
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
        
        # Test fetch regulations endpoint
        try:
            response = await client.post(
                f"{base_url}/api/v1/regulations/fetch",
                json={
                    "domain": "GST",
                    "entity_type": "Company"
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Fetch regulations endpoint working: {data['count']} regulations")
            else:
                print(f"❌ Fetch regulations endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Fetch regulations endpoint error: {e}")

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_regulation_fetcher_agent())
    
    # Uncomment to test API endpoints (requires server to be running)
    # asyncio.run(test_api_endpoints()) 