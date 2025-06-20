import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document, HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from core.config import settings
from models.mongo_models import Regulation, AgentExecutionLog
from database.mongo_database import get_database
import os
import shutil

logger = logging.getLogger(__name__)

# Global variables for agent state
vector_store = None
llm = None
embeddings = None
text_splitter = None
retrieval_qa_chain = None
contextual_retriever = None
is_initialized = False

def initialize_regulation_fetcher_agent():
    """Initialize the regulation fetcher agent components with full RAG pipeline"""
    global vector_store, llm, embeddings, text_splitter, retrieval_qa_chain, contextual_retriever, is_initialized
    
    try:
        logger.info("Starting Regulation Fetcher Agent initialization...")
        
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            temperature=0.7,
            top_p=0.85,
            google_api_key=settings.google_api_key,
        )
        logger.info("LLM initialized successfully")
        
        # Initialize embeddings (using HuggingFace instead of Google PaLM)
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        logger.info("Embeddings initialized successfully")
        
        # Initialize text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        logger.info("Text splitter initialized successfully")
        
        # Initialize ChromaDB vector store with error handling
        try:
            vector_store = Chroma(
                collection_name="tax_regulations",
                embedding_function=embeddings,
                persist_directory="./chroma_db"
            )
            logger.info("ChromaDB vector store initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            # Try to create a fresh vector store
            try:
                if os.path.exists("./chroma_db"):
                    shutil.rmtree("./chroma_db")
                vector_store = Chroma(
                    collection_name="tax_regulations",
                    embedding_function=embeddings,
                    persist_directory="./chroma_db"
                )
                logger.info("Fresh ChromaDB vector store created successfully")
            except Exception as e2:
                logger.error(f"Failed to create fresh ChromaDB: {e2}")
                return False
        
        # Initialize contextual compression retriever for better RAG
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
        logger.info("Contextual retriever initialized successfully")
        
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
        logger.info("RetrievalQA chain initialized successfully")
        
        is_initialized = True
        logger.info("Regulation Fetcher Agent with full RAG pipeline initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Regulation Fetcher Agent: {e}")
        is_initialized = False
        return False

def ensure_initialization():
    """Ensure the agent is initialized, re-initialize if needed"""
    global is_initialized
    if not is_initialized or vector_store is None or llm is None:
        logger.warning("Regulation Fetcher Agent not initialized, attempting to initialize...")
        return initialize_regulation_fetcher_agent()
    return True

async def fetch_regulations_agent(domain: str, entity_type: str) -> Dict[str, Any]:
    """Regulation Fetcher Agent - Fetch regulations for a specific domain and entity type"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Ensure agent is initialized
        if not ensure_initialization():
            return {
                "success": False,
                "error": "Failed to initialize Regulation Fetcher Agent",
                "execution_id": execution_id
            }
        
        # Log execution start
        await log_agent_execution_start(execution_id, "regulation_fetcher", {
            "domain": domain,
            "entity_type": entity_type
        })
        
        # Search existing regulations in MongoDB
        existing_regulations = await Regulation.find({
            "domain": domain,
            "entity_type": entity_type
        }).to_list()
        
        # Search vector store for relevant regulations
        vector_results = await search_vector_store_agent(domain, entity_type)
        
        # Combine and process results
        regulations = await process_regulations_agent(
            existing_regulations, vector_results, domain, entity_type
        )
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "regulation_fetcher", {
                "domain": domain,
                "entity_type": entity_type,
                "regulations_found": len(regulations)
            },
            execution_time
        )
        
        return {
            "success": True,
            "regulations": regulations,
            "count": len(regulations),
            "execution_id": execution_id
        }
        
    except Exception as e:
        logger.error(f"Error in fetch_regulations_agent: {e}")
        await log_agent_execution_error(execution_id, "regulation_fetcher", str(e))
        return {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }

async def rag_compliance_query_agent(query: str, domain: str = None, entity_type: str = None) -> Dict[str, Any]:
    """Full RAG Agent - Query tax compliance using retrieved context"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Ensure agent is initialized
        if not ensure_initialization():
            return {
                "success": False,
                "error": "Failed to initialize Regulation Fetcher Agent",
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
        if hasattr(result, 'source_documents'):
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

async def hybrid_search_agent(query: str, domain: str = None, entity_type: str = None) -> Dict[str, Any]:
    """Hybrid Search Agent - Combine vector and keyword search"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log execution start
        await log_agent_execution_start(execution_id, "hybrid_search", {
            "query": query,
            "domain": domain,
            "entity_type": entity_type
        })
        
        # Vector search
        vector_results = vector_store.similarity_search(query, k=5)
        
        # Keyword search (MongoDB)
        keyword_query = {}
        if domain:
            keyword_query["domain"] = domain
        if entity_type:
            keyword_query["entity_type"] = entity_type
        
        # Add text search if available
        if query:
            keyword_query["$text"] = {"$search": query}
        
        keyword_results = await Regulation.find(keyword_query).to_list()
        
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
                "score": 0.8  # Default score for keyword matches
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

async def search_vector_store_agent(domain: str, entity_type: str) -> List[Dict]:
    """Search vector store for relevant regulations"""
    global vector_store
    
    try:
        # Check if vector store is initialized, if not, initialize it
        if vector_store is None:
            logger.warning("Vector store not initialized, attempting to initialize...")
            success = initialize_regulation_fetcher_agent()
            if not success:
                logger.error("Failed to initialize vector store")
                return []
        
        query = f"tax regulations for {domain} applicable to {entity_type}"
        results = vector_store.similarity_search(query, k=10)
        
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": getattr(doc, 'score', 0.0)
            }
            for doc in results
        ]
    except Exception as e:
        logger.error(f"Error searching vector store: {e}")
        return []

async def process_regulations_agent(
    existing_regulations: List[Regulation], 
    vector_results: List[Dict], 
    domain: str, 
    entity_type: str
) -> List[Dict]:
    """Process and combine regulations from different sources"""
    processed_regulations = []
    seen_titles = set()  # Track seen titles to avoid duplicates
    
    # Process existing regulations from MongoDB
    for regulation in existing_regulations:
        if regulation.title not in seen_titles:
            processed_regulations.append({
                "id": str(regulation.id),
                "title": regulation.title,
                "content": regulation.content,
                "domain": regulation.domain,
                "entity_type": regulation.entity_type,
                "source_url": regulation.source_url,
                "version": regulation.version,
                "source": "database"
            })
            seen_titles.add(regulation.title)
    
    # Process vector store results
    for result in vector_results:
        title = result.get("metadata", {}).get("title", "Unknown Title")
        if title not in seen_titles:
            processed_regulations.append({
                "id": result.get("metadata", {}).get("id", f"vector_{len(processed_regulations)}"),
                "title": title,
                "content": result.get("content", result.get("page_content", "")),
                "domain": result.get("metadata", {}).get("domain", domain),
                "entity_type": result.get("metadata", {}).get("entity_type", entity_type),
                "source_url": result.get("metadata", {}).get("source_url", ""),
                "version": result.get("metadata", {}).get("version", "1.0"),
                "source": "vector_store"
            })
            seen_titles.add(title)
    
    # Sort by title for consistent ordering
    processed_regulations.sort(key=lambda x: x["title"])
    
    return processed_regulations

async def sync_regulations_agent(regulation_data: List[Dict]) -> Dict[str, Any]:
    """Sync regulations to both MongoDB and vector store"""
    execution_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    try:
        # Ensure agent is initialized
        if not ensure_initialization():
            return {
                "success": False,
                "error": "Failed to initialize Regulation Fetcher Agent",
                "execution_id": execution_id
            }
        
        # Log execution start
        await log_agent_execution_start(execution_id, "sync_regulations", {
            "regulations_count": len(regulation_data)
        })
        
        synced_count = 0
        errors = []
        
        for reg_data in regulation_data:
            try:
                # Create regulation object
                regulation = Regulation(**reg_data)
                await regulation.save()
                
                # Add to vector store
                await add_to_vector_store_agent(regulation)
                synced_count += 1
                
            except Exception as e:
                error_msg = f"Failed to sync regulation '{reg_data.get('title', 'Unknown')}': {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Log successful execution
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        await log_agent_execution_success(
            execution_id, "sync_regulations", {
                "regulations_synced": synced_count,
                "errors_count": len(errors)
            },
            execution_time
        )
        
        return {
            "success": True,
            "regulations_synced": synced_count,
            "errors": errors,
            "execution_id": execution_id
        }
        
    except Exception as e:
        logger.error(f"Error in sync_regulations_agent: {e}")
        await log_agent_execution_error(execution_id, "sync_regulations", str(e))
        return {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }

async def add_to_vector_store_agent(regulation: Regulation):
    """Add regulation to vector store for RAG"""
    try:
        global text_splitter
        
        # Ensure text_splitter is initialized
        if text_splitter is None:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
        
        # Create document for vector store
        doc = Document(
            page_content=regulation.content,
            metadata={
                "id": str(regulation.id),
                "title": regulation.title,
                "domain": regulation.domain,
                "entity_type": regulation.entity_type,
                "source_url": regulation.source_url,
                "version": regulation.version
            }
        )
        
        # Split document into chunks
        chunks = text_splitter.split_documents([doc])
        
        # Add to vector store
        if vector_store:
            vector_store.add_documents(chunks)
            logger.info(f"Added regulation '{regulation.title}' to vector store")
        else:
            logger.error("Vector store not available")
            
    except Exception as e:
        logger.error(f"Error adding to vector store: {e}")

async def log_agent_execution_start(execution_id: str, agent_name: str, input_data: Dict):
    """Log agent execution start"""
    log = AgentExecutionLog(
        agent_name=agent_name,
        execution_id=execution_id,
        input_data=input_data,
        status="In Progress"
    )
    await log.save()

async def log_agent_execution_success(execution_id: str, agent_name: str, output_data: Dict, execution_time: float):
    """Log successful agent execution"""
    log = await AgentExecutionLog.find_one({"execution_id": execution_id})
    if log:
        log.status = "Success"
        log.output_data = output_data
        log.execution_time = execution_time
        await log.save()

async def log_agent_execution_error(execution_id: str, agent_name: str, error_message: str):
    """Log failed agent execution"""
    log = await AgentExecutionLog.find_one({"execution_id": execution_id})
    if log:
        log.status = "Failed"
        log.error_message = error_message
        await log.save() 