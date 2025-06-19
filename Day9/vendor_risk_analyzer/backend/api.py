# FastAPI backend entry point

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
from backend.flows.vendor_risk_flow import run_vendor_risk_flow

app = FastAPI()

# Allow Streamlit (frontend) to call the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        result = run_vendor_risk_flow(file_location)
        os.remove(file_location)
        return result
    except Exception as e:
        return {"error": str(e)}
