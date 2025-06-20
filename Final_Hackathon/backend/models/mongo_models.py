from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from beanie import Document, Indexed
from pydantic import Field
from enum import Enum

def utc_now():
    """Get current UTC datetime with timezone info"""
    return datetime.now(timezone.utc)

class ComplianceStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"

class ValidationResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"

class AnomalyType(str, Enum):
    DUPLICATE = "duplicate"
    MISMATCH = "mismatch"
    SUSPICIOUS = "suspicious"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FilingStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    SUBMITTED = "submitted"

class Regulation(Document):
    """Tax regulation documents and rules"""
    title: str = Field(..., max_length=500)
    content: str
    domain: str = Field(..., max_length=100)  # GST, TDS, VAT, etc.
    entity_type: str = Field(..., max_length=100)  # Individual, Company, etc.
    source_url: Optional[str] = Field(max_length=500)
    effective_date: Optional[datetime]
    expiry_date: Optional[datetime]
    version: Optional[str] = Field(max_length=50)
    vector_id: Optional[str] = Field(max_length=255)  # Pinecone vector ID
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "regulations"
        indexes = [
            "domain",
            "entity_type",
            "effective_date",
            "vector_id"
        ]

class FinancialTransaction(Document):
    """Financial transaction records"""
    transaction_id: Indexed(str, unique=True)
    date: datetime
    amount: float
    description: Optional[str]
    category: Optional[str] = Field(max_length=100)
    tax_type: Optional[str] = Field(max_length=50)  # GST, TDS, VAT, etc.
    compliance_status: ComplianceStatus = Field(default=ComplianceStatus.PENDING)
    validation_notes: Optional[str]
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "financial_transactions"
        indexes = [
            "date",
            "tax_type",
            "compliance_status",
            "category"
        ]

class ComplianceValidation(Document):
    """Compliance validation results"""
    transaction_id: str
    regulation_id: str
    validation_result: ValidationResult
    validation_details: Optional[str]
    applied_rules: Optional[Dict[str, Any]]
    created_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "compliance_validations"
        indexes = [
            "transaction_id",
            "regulation_id",
            "validation_result"
        ]

class Anomaly(Document):
    """Detected anomalies"""
    transaction_id: str
    anomaly_type: AnomalyType
    severity: Severity
    description: str
    suggested_fix: Optional[str]
    status: str = Field(default="open", max_length=20)  # open, resolved, ignored
    created_at: datetime = Field(default_factory=utc_now)
    resolved_at: Optional[datetime]

    class Settings:
        name = "anomalies"
        indexes = [
            "transaction_id",
            "anomaly_type",
            "severity",
            "status"
        ]

class FilingReport(Document):
    """Generated filing reports"""
    report_id: Indexed(str, unique=True)
    filing_type: str = Field(max_length=100)  # GSTR-1, TDS, etc.
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    total_amount: Optional[float]
    tax_amount: Optional[float]
    status: FilingStatus = Field(default=FilingStatus.DRAFT)
    report_data: Optional[Dict[str, Any]]
    file_path: Optional[str] = Field(max_length=500)
    created_at: datetime = Field(default_factory=utc_now)
    submitted_at: Optional[datetime]

    class Settings:
        name = "filing_reports"
        indexes = [
            "filing_type",
            "status",
            "period_start",
            "period_end"
        ]

class AgentExecutionLog(Document):
    """Log of agent executions"""
    agent_name: str = Field(max_length=100)
    execution_id: Indexed(str, unique=True)
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]] = None
    status: str = Field(max_length=50)  # Success, Failed, In Progress
    error_message: Optional[str] = None
    execution_time: Optional[float] = None  # in seconds
    created_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "agent_execution_logs"
        indexes = [
            "agent_name",
            "status",
            "created_at"
        ] 