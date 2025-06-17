from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import shutil
from datetime import datetime
import logging
from document_processor import DocumentProcessor
from risk_analyzer import RiskAnalyzer
from data_enricher import DataEnricher
from scoring_engine import ScoringEngine
from report_generator import ReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vendor Risk Analyzer API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Create upload directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize components
document_processor = DocumentProcessor()
risk_analyzer = RiskAnalyzer()
data_enricher = DataEnricher()
scoring_engine = ScoringEngine()
report_generator = ReportGenerator()

@app.get("/")
async def read_root():
    with open("src/static/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.post("/analyze")
async def analyze_vendor(
    vendor_name: str = Form(...),
    gstin: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Analyze vendor documents for risk assessment
    """
    try:
        # Create vendor-specific directory
        vendor_dir = os.path.join(UPLOAD_DIR, f"{vendor_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(vendor_dir, exist_ok=True)
        
        # Save uploaded files
        saved_files = []
        for file in files:
            file_path = os.path.join(vendor_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file_path)
        
        # Process documents
        logger.info("Processing documents...")
        processed_docs = document_processor.process_documents(saved_files)
        
        # Risk Analysis
        logger.info("Analyzing risks...")
        risk_analysis = risk_analyzer.analyze(processed_docs)
        
        # Data Enrichment
        logger.info("Enriching data...")
        enriched_data = data_enricher.enrich_data(processed_docs, risk_analysis)

        # Calculate risk score
        logger.info("Calculating risk score...")
        risk_score = scoring_engine.calculate_score({
            "document_analysis": processed_docs,
            "risk_analysis": risk_analysis,
            "enriched_data": enriched_data
        })

        # Generate report
        logger.info("Generating report...")
        vendor_info = {"name": vendor_name, "gstin": gstin}
        report = report_generator.generate_report(vendor_info, {"document_analysis": processed_docs, "risk_analysis": risk_analysis, "enriched_data": enriched_data}, risk_score)

        # Prepare final response
        final_response = {
            "vendor_info": {
                "name": vendor_name,
                "gstin": gstin,
                "analysis_date": datetime.now().isoformat()
            },
            "document_analysis": {
                "total_documents": processed_docs["total_documents"],
                "processed_documents": processed_docs["processed_documents"]
            },
            "risk_analysis": risk_analysis,
            "enriched_data": enriched_data,
            "risk_score": risk_score,
            "report": report
        }
        
        # Clean up uploaded files
        shutil.rmtree(vendor_dir)
        
        return JSONResponse(content=final_response)
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        # Clean up in case of error
        if os.path.exists(vendor_dir):
            shutil.rmtree(vendor_dir)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("Starting Vendor Risk Analyzer API...")
    print("Open http://127.0.0.1:3001 in your browser")
    uvicorn.run(app, host="127.0.0.1", port=3001) 