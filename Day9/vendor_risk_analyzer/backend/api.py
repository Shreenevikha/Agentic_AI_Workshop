# FastAPI backend entry point

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
from backend.flows.vendor_risk_flow import run_vendor_risk_flow
from backend.retriever.retriever_pipeline import get_retriever
from backend.data.sample_knowledge_base import initialize_sample_knowledge_base

app = FastAPI()

# Allow Streamlit (frontend) to call the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG system with sample knowledge base
@app.on_event("startup")
async def startup_event():
    """Initialize the RAG system on startup."""
    try:
        print("Initializing RAG system...")
        retriever = get_retriever()
        initialize_sample_knowledge_base(retriever)
        print("RAG system initialized successfully!")
    except Exception as e:
        print(f"Error initializing RAG system: {e}")

@app.get("/")
def read_root():
    return {"message": "Vendor Risk Analyzer backend is running!"}

@app.post("/analyze/")
async def analyze_vendor(file: UploadFile = File(...)):
    try:
        file_location = f"backend/data/{file.filename}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as f:
            f.write(await file.read())
        
        # Run the complete agent-based workflow
        result = run_vendor_risk_flow(file_location)
        
        # Clean up uploaded file
        os.remove(file_location)
        
        return result
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Vendor Risk Analyzer is operational",
        "agents": {
            "document_analysis": "ready",
            "risk_signal_detection": "ready", 
            "external_intelligence": "ready",
            "credibility_scoring": "ready"
        },
        "rag_system": "initialized"
    }
