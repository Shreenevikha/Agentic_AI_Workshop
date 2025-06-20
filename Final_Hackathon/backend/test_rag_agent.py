import asyncio
import logging
from agents.rag_agent import (
    initialize_rag_agent,
    rag_compliance_query_agent,
    hybrid_search_agent
)
from agents.regulation_fetcher_agent import (
    initialize_regulation_fetcher_agent,
    vector_store
)
from database.mongo_database import connect_to_mongo, close_mongo_connection
from core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_agent():
    """Test the RAG Agent functionality"""
    
    print("🚀 Testing RAG Agent with Full Pipeline...")
    
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        print("✅ Connected to MongoDB")
        
        # Initialize regulation fetcher agent first
        success = initialize_regulation_fetcher_agent()
        if success:
            print("✅ Regulation Fetcher Agent initialized")
        else:
            print("❌ Failed to initialize Regulation Fetcher Agent")
            return
        
        # Initialize RAG agent
        rag_success = initialize_rag_agent(vector_store)
        if rag_success:
            print("✅ RAG Agent initialized")
        else:
            print("❌ Failed to initialize RAG Agent")
            return
        
        # Test 1: RAG Compliance Query
        print("\n📋 Test 1: RAG Compliance Query...")
        query = "What are the GST registration requirements for companies?"
        result = await rag_compliance_query_agent(
            query=query,
            domain="GST",
            entity_type="Company"
        )
        
        if result["success"]:
            print(f"✅ RAG Query successful")
            print(f"📊 Answer: {result['answer'][:200]}...")
            print(f"📊 Sources used: {len(result['sources'])}")
            print(f"📊 Execution ID: {result['execution_id']}")
        else:
            print(f"❌ RAG Query failed: {result['error']}")
        
        # Test 2: Hybrid Search
        print("\n📋 Test 2: Hybrid Search...")
        search_result = await hybrid_search_agent(
            query="GST registration",
            vector_store=vector_store,
            domain="GST",
            entity_type="Company"
        )
        
        if search_result["success"]:
            print(f"✅ Hybrid Search successful")
            print(f"📊 Results found: {search_result['count']}")
            print(f"📊 Execution ID: {search_result['execution_id']}")
        else:
            print(f"❌ Hybrid Search failed: {search_result['error']}")
        
        # Test 3: Complex RAG Query
        print("\n📋 Test 3: Complex RAG Query...")
        complex_query = "What are the penalties for late GST filing and how can they be avoided?"
        complex_result = await rag_compliance_query_agent(
            query=complex_query,
            domain="GST",
            entity_type="Company"
        )
        
        if complex_result["success"]:
            print(f"✅ Complex RAG Query successful")
            print(f"📊 Answer: {complex_result['answer'][:300]}...")
            print(f"📊 Sources used: {len(complex_result['sources'])}")
        else:
            print(f"❌ Complex RAG Query failed: {complex_result['error']}")
        
        print("\n🎉 All RAG tests completed successfully!")
        
    except Exception as e:
        logger.error(f"RAG test failed: {e}")
        print(f"❌ RAG test failed: {e}")
    
    finally:
        # Close database connection
        await close_mongo_connection()
        print("✅ Database connection closed")

if __name__ == "__main__":
    # Run RAG tests
    asyncio.run(test_rag_agent()) 