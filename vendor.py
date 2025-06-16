from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Vendor(BaseModel):
    name: str
    gstin: str
    pan: Optional[str] = None
    documents: List[str] = Field(default_factory=list)
    risk_score: float = 0.0
    risk_factors: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True

    def add_risk_factor(self, factor: str, weight: float = 1.0):
        """Add a risk factor and update the risk score"""
        self.risk_factors.append(factor)
        self.risk_score = min(100, self.risk_score + weight)
        
    def add_document(self, document_path: str):
        """Add a document to the vendor's document list"""
        self.documents.append(document_path)
        
    def get_risk_summary(self) -> dict:
        """Get a summary of the vendor's risk assessment"""
        return {
            "name": self.name,
            "gstin": self.gstin,
            "risk_score": self.risk_score,
            "risk_factors": self.risk_factors,
            "last_updated": self.last_updated.isoformat()
        } 