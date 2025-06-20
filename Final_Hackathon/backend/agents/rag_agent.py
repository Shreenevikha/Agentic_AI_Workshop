import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from core.config import settings
from models.mongo_models import Regulation, AgentExecutionLog
from database.mongo_database import get_database

logger = logging.getLogger(__name__)

# Global variables for RAG components
llm = None
retrieval_qa_chain = None
contextual_retriever = None
is_initialized = False

def initialize_rag_agent(vector_store):
    """Initialize RAG agent with full pipeline"""
    global llm, retrieval_qa_chain, contextual_retriever, is_initialized
    
    try:
        if not vector_store:
            logger.error("Vector store is required for RAG agent initialization")
            return False
            
        # Initialize Gemini LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            temperature=0.7,
            top_p=0.85,
            google_api_key=settings.google_api_key
        )
        
        # Initialize contextual compression retriever
        compressor_prompt = PromptTemplate(
            input_variables=["question", "context"],
            template="""Given the following question and context, extract only the relevant information that helps answer the question.

Question: {question}
Context: {context}

Relevant information:"""
        )
        
        compressor = LLMChainExtractor.from_llm(llm, compressor_prompt)
        contextual_retriever = ContextualCompressionRetriever(
            base_retriever=vector_store.as_retriever(search_kwargs={"k": 10}),
            base_compressor=compressor
        )
        
        # Initialize RetrievalQA chain for full RAG
        qa_prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a tax compliance expert. Use the following tax regulations to answer the question accurately.

Tax Regulations Context:
{context}

Question: {question}

Please provide a comprehensive answer based on the regulations above. If the information is not available in the context, say so clearly.

Answer:"""
        )
        
        retrieval_qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=contextual_retriever,
            chain_type_kwargs={"prompt": qa_prompt_template},
            return_source_documents=True
        )
        
        is_initialized = True
        logger.info("RAG Agent initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize RAG Agent: {e}")
        is_initialized = False
        return False

def ensure_rag_initialization(vector_store):
    """Ensure RAG agent is initialized, re-initialize if needed"""
    global is_initialized
    if not is_initialized or retrieval_qa_chain is None or llm is None:
        logger.warning("RAG Agent not initialized, attempting to initialize...")
        return initialize_rag_agent(vector_store)
    return True

async def rag_compliance_query_agent(query: str, domain: str = None, entity_type: str = None) -> Dict[str, Any]:
    """Full RAG Agent - Query tax compliance using retrieved context"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Import vector store from regulation fetcher
        from agents.regulation_fetcher_agent import vector_store as reg_vector_store
        
        # Check if vector store is available
        if not reg_vector_store:
            return {
                "success": False,
                "error": "Vector store not available. Please ensure regulation fetcher agent is initialized first.",
                "execution_id": execution_id
            }
        
        # Ensure RAG agent is initialized
        if not ensure_rag_initialization(reg_vector_store):
            return {
                "success": False,
                "error": "Failed to initialize RAG agent",
                "execution_id": execution_id
            }
        
        # Log execution start
        await log_agent_execution_start(execution_id, "rag_compliance_query", {
            "query": query,
            "domain": domain,
            "entity_type": entity_type
        })
        
        # Build enhanced query with domain context
        enhanced_query = query
        if domain and entity_type:
            enhanced_query = f"Regarding {domain} regulations for {entity_type}: {query}"
        
        # Use RetrievalQA chain for full RAG
        result = retrieval_qa_chain({"query": enhanced_query})
        
        # Extract source documents
        source_docs = []
        if hasattr(result, 'source_documents') and result['source_documents']:
            for doc in result['source_documents']:
                source_docs.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": getattr(doc, 'score', 0.0)
                })
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "rag_compliance_query", {
                "query": query,
                "sources_used": len(source_docs)
            },
            execution_time
        )
        
        return {
            "success": True,
            "answer": result['result'],
            "sources": source_docs,
            "execution_id": execution_id
        }
        
    except Exception as e:
        logger.error(f"Error in rag_compliance_query_agent: {e}")
        await log_agent_execution_error(execution_id, "rag_compliance_query", str(e))
        return {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }

async def hybrid_search_agent(query: str, vector_store, domain: str = None, entity_type: str = None) -> Dict[str, Any]:
    """Hybrid Search Agent - Combine vector and keyword search"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Check if vector store is available
        if not vector_store:
            return {
                "success": False,
                "error": "Vector store not available for hybrid search",
                "execution_id": execution_id
            }
        
        # Log execution start
        await log_agent_execution_start(execution_id, "hybrid_search", {
            "query": query,
            "domain": domain,
            "entity_type": entity_type
        })
        
        # Vector search
        try:
            vector_results = vector_store.similarity_search(query, k=5)
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            vector_results = []
        
        # Keyword search (MongoDB)
        keyword_query = {}
        if domain:
            keyword_query["domain"] = domain
        if entity_type:
            keyword_query["entity_type"] = entity_type
        
        try:
            keyword_results = await Regulation.find(keyword_query).to_list()
        except Exception as e:
            logger.warning(f"Keyword search failed: {e}")
            keyword_results = []
        
        # Combine and rank results
        combined_results = []
        
        # Add vector results
        for doc in vector_results:
            combined_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "source": "vector_search",
                "score": getattr(doc, 'score', 0.0)
            })
        
        # Add keyword results
        for reg in keyword_results:
            combined_results.append({
                "content": reg.content,
                "metadata": {
                    "id": str(reg.id),
                    "title": reg.title,
                    "domain": reg.domain,
                    "entity_type": reg.entity_type
                },
                "source": "keyword_search",
                "score": 0.8
            })
        
        # Remove duplicates and sort by score
        seen_contents = set()
        unique_results = []
        for result in combined_results:
            if result["content"] not in seen_contents:
                seen_contents.add(result["content"])
                unique_results.append(result)
        
        unique_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "hybrid_search", {
                "query": query,
                "results_found": len(unique_results)
            },
            execution_time
        )
        
        return {
            "success": True,
            "results": unique_results,
            "count": len(unique_results),
            "execution_id": execution_id
        }
        
    except Exception as e:
        logger.error(f"Error in hybrid_search_agent: {e}")
        await log_agent_execution_error(execution_id, "hybrid_search", str(e))
        return {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }

async def log_agent_execution_start(execution_id: str, agent_name: str, input_data: Dict):
    """Log the start of an agent execution"""
    try:
        log_entry = AgentExecutionLog(
            execution_id=execution_id,
            agent_name=agent_name,
            status="running",
            start_time=datetime.now(timezone.utc),
            end_time=None,
            input_data=input_data,
            output_data=None,
            error_message=None,
            execution_time=None
        )
        await log_entry.save()
    except Exception as e:
        logger.error(f"Error logging agent execution start: {e}")

async def log_agent_execution_success(execution_id: str, agent_name: str, output_data: Dict, execution_time: float):
    """Log the successful completion of an agent execution"""
    try:
        log_entry = await AgentExecutionLog.find_one({"execution_id": execution_id})
        if log_entry:
            log_entry.status = "success"
            log_entry.end_time = datetime.now(timezone.utc)
            log_entry.output_data = output_data
            log_entry.execution_time = execution_time
            await log_entry.save()
    except Exception as e:
        logger.error(f"Error logging agent execution success: {e}")

async def log_agent_execution_error(execution_id: str, agent_name: str, error_message: str):
    """Log an error during agent execution"""
    try:
        log_entry = await AgentExecutionLog.find_one({"execution_id": execution_id})
        if log_entry:
            log_entry.status = "error"
            log_entry.end_time = datetime.now(timezone.utc)
            log_entry.error_message = error_message
            await log_entry.save()
    except Exception as e:
        logger.error(f"Error logging agent execution error: {e}") 