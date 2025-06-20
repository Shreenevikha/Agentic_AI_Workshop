import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuration settings for the application"""
    
    def __init__(self):
        # Google Gemini Configuration
        self.google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
        
        # Database Configuration - MongoDB
        self.mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/tax_compliance")
        
        # API Configuration
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        self.debug: bool = os.getenv("DEBUG", "True").lower() == "true"
        
        # Security
        self.secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
        self.jwt_secret: str = os.getenv("JWT_SECRET", "your-jwt-secret-here")
        
        # External APIs
        self.government_api_key: Optional[str] = os.getenv("GOVERNMENT_API_KEY")
        self.tax_portal_api_url: str = os.getenv("TAX_PORTAL_API_URL", "https://api.taxportal.gov.in")
        
        # Logging
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings() 