"""
Environment Setup Script for Vendor Risk Analyzer
Helps users set up their Gemini API key and test the system.
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Set up environment variables for the application."""
    print("🔧 Vendor Risk Analyzer - Environment Setup")
    print("=" * 50)
    
    # Check if GEMINI_API_KEY is already set
    current_key = os.getenv("GEMINI_API_KEY")
    
    if current_key:
        print(f"✅ GEMINI_API_KEY is already set: {current_key[:10]}...")
        return True
    
    print("❌ GEMINI_API_KEY not found in environment variables.")
    print("\n📝 To set up your Gemini API key, you have several options:")
    print("\n1️⃣  **Set Environment Variable (Recommended)**")
    print("   Windows (PowerShell):")
    print("   $env:GEMINI_API_KEY='your-api-key-here'")
    print("\n   Windows (Command Prompt):")
    print("   set GEMINI_API_KEY=your-api-key-here")
    print("\n   Linux/Mac:")
    print("   export GEMINI_API_KEY='your-api-key-here'")
    
    print("\n2️⃣  **Create .env file**")
    print("   Create a file named '.env' in the project root with:")
    print("   GEMINI_API_KEY=your-api-key-here")
    
    print("\n3️⃣  **Pass directly when running**")
    print("   GEMINI_API_KEY=your-key python test_agents.py")
    
    print("\n🔑 **To get a Gemini API key:**")
    print("   1. Go to https://makersuite.google.com/app/apikey")
    print("   2. Sign in with your Google account")
    print("   3. Click 'Create API Key'")
    print("   4. Copy the generated API key")
    print("   5. Use the key above")
    
    # Ask user if they want to set it now
    response = input("\n🤔 Would you like to set the API key now? (y/n): ").lower().strip()
    
    if response == 'y':
        api_key = input("🔑 Enter your Gemini API key: ").strip()
        if api_key:
            # Set environment variable for current session
            os.environ["GEMINI_API_KEY"] = api_key
            print("✅ API key set for current session!")
            
            # Create .env file for future sessions
            env_file = Path(__file__).parent / ".env"
            try:
                with open(env_file, "w") as f:
                    f.write(f"GEMINI_API_KEY={api_key}\n")
                print(f"✅ Created .env file at {env_file}")
                return True
            except Exception as e:
                print(f"⚠️  Could not create .env file: {e}")
                return True
        else:
            print("❌ No API key provided.")
            return False
    else:
        print("ℹ️  You can set the API key later and run the system with fallback methods.")
        return False

def test_system():
    """Test the system with current configuration."""
    print("\n🧪 Testing System Configuration")
    print("=" * 50)
    
    # Test config import
    try:
        sys.path.append(str(Path(__file__).parent))
        from config import config
        
        if config.is_gemini_available():
            print("✅ Gemini API key is available")
            print(f"   Model: {config.gemini_model}")
            print(f"   Temperature: {config.temperature}")
        else:
            print("⚠️  Gemini API key not available - using fallback methods")
        
        # Test basic imports
        print("\n📦 Testing imports...")
        
        # Test backend imports
        sys.path.append(str(Path(__file__).parent / "backend"))
        
        try:
            from backend.document_analysis_agent import get_document_analysis_agent
            print("✅ Document Analysis Agent imported")
        except Exception as e:
            print(f"❌ Document Analysis Agent import failed: {e}")
        
        try:
            from backend.external_intelligence_agent import get_external_intelligence_agent
            print("✅ External Intelligence Agent imported")
        except Exception as e:
            print(f"❌ External Intelligence Agent import failed: {e}")
        
        try:
            from backend.retriever.retriever_pipeline import get_retriever
            print("✅ RAG Retriever imported")
        except Exception as e:
            print(f"❌ RAG Retriever import failed: {e}")
        
        print("\n🎉 System configuration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Vendor Risk Analyzer Setup")
    print("=" * 50)
    
    # Setup environment
    env_ok = setup_environment()
    
    # Test system
    test_ok = test_system()
    
    print("\n" + "=" * 50)
    print("📋 Setup Summary")
    print("=" * 50)
    
    if env_ok:
        print("✅ Environment setup completed")
    else:
        print("⚠️  Environment setup incomplete - API key needed for full functionality")
    
    if test_ok:
        print("✅ System test passed")
    else:
        print("❌ System test failed")
    
    print("\n🎯 Next Steps:")
    if env_ok and test_ok:
        print("1. Run: python test_agents.py")
        print("2. Run: cd backend && uvicorn api:app --reload")
        print("3. Open browser to: http://localhost:8000")
    else:
        print("1. Set your Gemini API key using one of the methods above")
        print("2. Run this script again: python setup_env.py")
        print("3. Then run: python test_agents.py")
    
    print("\n💡 Note: The system will work with fallback methods even without Gemini API key!")

if __name__ == "__main__":
    main() 