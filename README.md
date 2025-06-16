# Vendor Risk Analyzer

A comprehensive solution for analyzing vendor risk using AI agents. This system helps finance teams evaluate vendors by analyzing documents, assessing risks, and providing a credibility score.

## Features

- Document Analysis: Scans vendor invoices and contracts for key information
- Risk Assessment: Evaluates financial and compliance risks
- Data Enrichment: Gathers additional information from public sources
- Credibility Scoring: Generates a comprehensive risk score for vendors

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd vendor_risk_analyzer
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Start the server:
```bash
python src/main.py
```

2. The API will be available at `http://localhost:8000`

3. Use the `/analyze-vendor` endpoint to analyze vendor documents:
```bash
curl -X POST "http://localhost:8000/analyze-vendor" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "name=Vendor Name" \
     -F "gstin=GSTIN123456789" \
     -F "documents=@path/to/document1.pdf" \
     -F "documents=@path/to/document2.pdf"
```

## API Endpoints

- `POST /analyze-vendor`: Analyze vendor documents and generate risk assessment
- `GET /health`: Check API health status

## Response Format

The `/analyze-vendor` endpoint returns a JSON response with the following structure:
```json
{
    "name": "Vendor Name",
    "gstin": "GSTIN123456789",
    "risk_score": 75.5,
    "risk_factors": [
        "Inconsistent billing patterns",
        "Expired GSTIN",
        "Low credit score"
    ],
    "last_updated": "2024-01-01T12:00:00"
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 