"""
Compliance Validator Agent
Validates transaction entries against current tax rules and flags non-compliant entries
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from core.config import settings
from models.mongo_models import FinancialTransaction, ComplianceValidation, Regulation
from database.mongo_database import get_database

logger = logging.getLogger(__name__)

# Global variables
llm = None

def initialize_compliance_validator_agent():
    """Initialize the compliance validator agent"""
    global llm
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            temperature=0.3,
            google_api_key=settings.google_api_key
        )
        
        logger.info("Compliance Validator Agent initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Compliance Validator Agent: {e}")
        return False

async def validate_transaction_agent(transaction: FinancialTransaction, regulations: List[Regulation]) -> Dict[str, Any]:
    """Validate a single transaction against regulations"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "compliance_validator", {
            "transaction_id": transaction.transaction_id,
            "amount": transaction.amount,
            "tax_type": transaction.tax_type
        })
        
        # Initialize LLM if not already done
        if llm is None:
            initialize_compliance_validator_agent()
        
        # Build validation context from regulations
        regulation_context = ""
        for reg in regulations:
            regulation_context += f"Regulation: {reg.title}\n{reg.content}\n\n"
        
        # Create validation prompt
        validation_prompt = PromptTemplate(
            input_variables=["transaction", "regulations"],
            template="""You are a tax compliance expert. Validate the following transaction against the provided tax regulations.

Transaction Details:
- Amount: {transaction_amount}
- Description: {transaction_description}
- Category: {transaction_category}
- Tax Type: {transaction_tax_type}
- Date: {transaction_date}

Tax Regulations:
{regulations}

Please analyze this transaction and provide:
1. Compliance Status: MUST be one of 'valid', 'invalid', or 'pending'.
2. Validation Details: Specific reasons for the status.
3. Applied Rules: A dictionary of regulations that were applied.

Format your response as a single, clean JSON object:
{{
    "status": "valid|invalid|pending",
    "details": "Detailed explanation",
    "applied_rules": {{"rule1": "description"}}
}}"""
        )
        
        # Prepare transaction data
        transaction_data = {
            "transaction_amount": transaction.amount,
            "transaction_description": transaction.description or "No description",
            "transaction_category": transaction.category or "Uncategorized",
            "transaction_tax_type": transaction.tax_type or "Unknown",
            "transaction_date": transaction.date.isoformat() if transaction.date else "Unknown",
            "regulations": regulation_context
        }
        
        # Get validation from LLM
        prompt = validation_prompt.format(**transaction_data)
        response = await llm.ainvoke([{"role": "user", "content": prompt}])
        
        validation_result = parse_validation_response(response.content)

        # --- Definitive Status Mapping ---
        status_map = {
            "pass": "valid", "valid": "valid",
            "fail": "invalid", "invalid": "invalid",
            "warning": "pending", "pending": "pending"
        }
        raw_status = validation_result.get("status", "pending").lower()
        final_status = status_map.get(raw_status, "pending") # Default to 'pending' if unknown status
        # --- End of Mapping ---

        if isinstance(validation_result.get("applied_rules"), list):
            validation_result["applied_rules"] = {rule: "" for rule in validation_result["applied_rules"]}
        
        validation = ComplianceValidation(
            transaction_id=transaction.transaction_id,
            regulation_id="",
            validation_result=final_status, # Use the cleaned status
            validation_details=validation_result.get("details", "No details provided."),
            applied_rules=validation_result.get("applied_rules", {})
        )
        if MongoDB.is_connected:
            await validation.save()
        
        transaction.compliance_status = final_status # Use the cleaned status
        transaction.validation_notes = validation_result.get("details", "No details provided.")
        if MongoDB.is_connected:
            await transaction.save()
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "compliance_validator", {
                "transaction_id": transaction.transaction_id,
                "validation_status": final_status,
                "flags_count": len(validation_result.get("flags", []))
            },
            execution_time
        )
        
        return {
            "success": True,
            "transaction_id": transaction.transaction_id,
            "validation_result": {**validation_result, "status": final_status},
            "execution_id": execution_id
        }
        
    except Exception as e:
        logger.error(f"Error in validate_transaction_agent: {e}")
        # Log the raw response for debugging
        if 'response' in locals():
            logger.error(f"Raw LLM response was: {response.content}")
        await log_agent_execution_error(execution_id, "compliance_validator", str(e))
        return {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }

async def validate_batch_transactions_agent(transactions: List[FinancialTransaction], domain: str, entity_type: str) -> Dict[str, Any]:
    """Validate multiple transactions against regulations"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "batch_compliance_validator", {
            "transactions_count": len(transactions),
            "domain": domain,
            "entity_type": entity_type
        })
        
        # Get relevant regulations
        regulations = await Regulation.find({
            "domain": domain,
            "entity_type": entity_type
        }).to_list()
        
        # Validate each transaction
        validation_results = []
        valid_count = 0
        invalid_count = 0
        pending_count = 0
        
        for transaction in transactions:
            result = await validate_transaction_agent(transaction, regulations)
            if result["success"]:
                validation_results.append(result)
                status = result["validation_result"]["status"]
                if status == "valid":
                    valid_count += 1
                elif status == "invalid":
                    invalid_count += 1
                else:
                    pending_count += 1
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "batch_compliance_validator", {
                "total_transactions": len(transactions),
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "pending_count": pending_count
            },
            execution_time
        )
        
        return {
            "success": True,
            "validation_results": validation_results,
            "summary": {
                "total": len(transactions),
                "valid": valid_count,
                "invalid": invalid_count,
                "pending": pending_count
            },
            "execution_id": execution_id
        }
        
    except Exception as e:
        logger.error(f"Error in validate_batch_transactions_agent: {e}")
        await log_agent_execution_error(execution_id, "batch_compliance_validator", str(e))
        return {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }

async def flag_invalid_entries_agent(transactions: List[FinancialTransaction]) -> Dict[str, Any]:
    """Flag invalid entries with specific reasons"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "flag_invalid_entries", {
            "transactions_count": len(transactions)
        })
        
        flagged_entries = []
        
        for transaction in transactions:
            if transaction.compliance_status == "invalid":
                # Analyze the validation notes to extract specific flags
                flags = extract_flags_from_validation(transaction.validation_notes)
                
                flagged_entries.append({
                    "transaction_id": transaction.transaction_id,
                    "amount": transaction.amount,
                    "description": transaction.description,
                    "tax_type": transaction.tax_type,
                    "validation_notes": transaction.validation_notes,
                    "flags": flags,
                    "suggestions": extract_suggestions_from_validation(transaction.validation_notes)
                })
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "flag_invalid_entries", {
                "flagged_count": len(flagged_entries)
            },
            execution_time
        )
        
        return {
            "success": True,
            "flagged_entries": flagged_entries,
            "count": len(flagged_entries),
            "execution_id": execution_id
        }
        
    except Exception as e:
        logger.error(f"Error in flag_invalid_entries_agent: {e}")
        await log_agent_execution_error(execution_id, "flag_invalid_entries", str(e))
        return {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }

def parse_validation_response(response_text: str) -> Dict[str, Any]:
    """Parse LLM response into structured validation result"""
    try:
        # Simple parsing for demo - in production, use proper JSON parsing
        if "pass" in response_text.lower():
            status = "pass"
        elif "fail" in response_text.lower():
            status = "fail"
        else:
            status = "warning"
        
        return {
            "status": status,
            "details": response_text,
            "applied_rules": ["GST Registration Rules", "ITC Eligibility Rules"],
            "suggestions": ["Verify GSTIN", "Check invoice format"],
            "flags": ["Missing PAN", "Invalid GSTIN"] if status == "fail" else []
        }
    except Exception as e:
        logger.error(f"Error parsing validation response: {e}")
        return {
            "status": "warning",
            "details": "Error parsing validation response",
            "applied_rules": [],
            "suggestions": ["Manual review required"],
            "flags": ["Parsing error"]
        }

def extract_flags_from_validation(validation_notes: str) -> List[str]:
    """Extract specific flags from validation notes"""
    flags = []
    if validation_notes:
        # Simple flag extraction - in production, use NLP
        if "PAN" in validation_notes.upper():
            flags.append("Missing PAN")
        if "GSTIN" in validation_notes.upper():
            flags.append("Invalid GSTIN")
        if "THRESHOLD" in validation_notes.upper():
            flags.append("Exceeds threshold")
        if "INVOICE" in validation_notes.upper():
            flags.append("Invoice format issue")
    return flags

def extract_suggestions_from_validation(validation_notes: str) -> List[str]:
    """Extract suggestions from validation notes"""
    suggestions = []
    if validation_notes:
        # Simple suggestion extraction
        if "PAN" in validation_notes.upper():
            suggestions.append("Add PAN number to invoice")
        if "GSTIN" in validation_notes.upper():
            suggestions.append("Verify GSTIN format")
        if "THRESHOLD" in validation_notes.upper():
            suggestions.append("Split transaction if possible")
    return suggestions

async def log_agent_execution_start(execution_id: str, agent_name: str, input_data: Dict):
    """Log agent execution start"""
    from models.mongo_models import AgentExecutionLog
    
    log = AgentExecutionLog(
        agent_name=agent_name,
        execution_id=execution_id,
        input_data=input_data,
        status="In Progress"
    )
    await log.save()

async def log_agent_execution_success(execution_id: str, agent_name: str, output_data: Dict, execution_time: float):
    """Log successful agent execution"""
    from models.mongo_models import AgentExecutionLog
    
    log = await AgentExecutionLog.find_one({"execution_id": execution_id})
    if log:
        log.status = "Success"
        log.output_data = output_data
        log.execution_time = execution_time
        await log.save()

async def log_agent_execution_error(execution_id: str, agent_name: str, error_message: str):
    """Log failed agent execution"""
    from models.mongo_models import AgentExecutionLog
    
    log = await AgentExecutionLog.find_one({"execution_id": execution_id})
    if log:
        log.status = "Failed"
        log.error_message = error_message
        await log.save() 