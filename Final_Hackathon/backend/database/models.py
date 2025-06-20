from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Regulation(Base):
    """Tax regulation documents and rules"""
    __tablename__ = "regulations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    domain = Column(String(100), nullable=False)  # GST, TDS, VAT, etc.
    entity_type = Column(String(100), nullable=False)  # Individual, Company, etc.
    source_url = Column(String(500))
    effective_date = Column(DateTime)
    expiry_date = Column(DateTime)
    version = Column(String(50))
    vector_id = Column(String(255))  # Pinecone vector ID
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class FinancialTransaction(Base):
    """Financial transaction records"""
    __tablename__ = "financial_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(255), unique=True, nullable=False)
    date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(Text)
    category = Column(String(100))
    tax_type = Column(String(50))  # GST, TDS, VAT, etc.
    compliance_status = Column(String(50))  # Valid, Invalid, Pending
    validation_notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ComplianceValidation(Base):
    """Compliance validation results"""
    __tablename__ = "compliance_validations"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("financial_transactions.id"))
    regulation_id = Column(Integer, ForeignKey("regulations.id"))
    validation_result = Column(String(50))  # Pass, Fail, Warning
    validation_details = Column(Text)
    applied_rules = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    
    transaction = relationship("FinancialTransaction")
    regulation = relationship("Regulation")

class Anomaly(Base):
    """Detected anomalies"""
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("financial_transactions.id"))
    anomaly_type = Column(String(100))  # Duplicate, Mismatch, Suspicious
    severity = Column(String(20))  # Low, Medium, High, Critical
    description = Column(Text)
    suggested_fix = Column(Text)
    status = Column(String(20), default="Open")  # Open, Resolved, Ignored
    created_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)
    
    transaction = relationship("FinancialTransaction")

class FilingReport(Base):
    """Generated filing reports"""
    __tablename__ = "filing_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(255), unique=True, nullable=False)
    filing_type = Column(String(100))  # GSTR-1, TDS, etc.
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    total_amount = Column(Float)
    tax_amount = Column(Float)
    status = Column(String(50))  # Draft, Ready, Submitted
    report_data = Column(JSON)
    file_path = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    submitted_at = Column(DateTime)

class AgentExecutionLog(Base):
    """Log of agent executions"""
    __tablename__ = "agent_execution_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), nullable=False)
    execution_id = Column(String(255), unique=True, nullable=False)
    input_data = Column(JSON)
    output_data = Column(JSON)
    status = Column(String(50))  # Success, Failed, In Progress
    error_message = Column(Text)
    execution_time = Column(Float)  # in seconds
    created_at = Column(DateTime, default=func.now()) 