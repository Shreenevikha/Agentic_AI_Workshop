"""
Configuration file for Vendor Risk Analyzer
Handles API keys and provides fallback mechanisms.
"""

import os
from typing import Optional

class Config:
    """Configuration class for the application."""
    
    def __init__(self):
        self.gemini_api_key = self._get_gemini_api_key()
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-pro")
        self.temperature = float(os.getenv("TEMPERATURE", "0"))
    
    def _get_gemini_api_key(self) -> Optional[str]:
        """Get Gemini API key from environment or prompt user."""
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            print("⚠️  WARNING: GEMINI_API_KEY not found in environment variables!")
            print("📝 To fix this, you can:")
            print("   1. Set the environment variable: export GEMINI_API_KEY='your-key'")
            print("   2. Create a .env file with: GEMINI_API_KEY=your-key")
            print("   3. Pass the key directly when running the application")
            print("\n🔄 The system will use fallback methods for now...")
            return None
        
        return api_key
    
    def is_gemini_available(self) -> bool:
        """Check if Gemini API is available."""
        return self.gemini_api_key is not None
    
    def get_gemini_config(self) -> dict:
        """Get Gemini configuration."""
        if not self.is_gemini_available():
            raise ValueError("Gemini API key not available")
        
        return {
            "api_key": self.gemini_api_key,
            "model": self.gemini_model,
            "temperature": self.temperature
        }

# Global configuration instance
config = Config() 