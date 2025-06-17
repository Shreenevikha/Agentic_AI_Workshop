# Vendor Risk Analyzer

An AI-powered system for evaluating vendor credibility and compliance risk using RAG and LangChain.

## Features

- Document Analysis: Extracts key information from vendor documents
- Risk Signal Detection: Identifies potential risks and anomalies
- Credibility Scoring: Generates comprehensive risk assessments with justifications

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Place vendor documents in a directory accessible to the system.

2. Run the analyzer:
```bash
python main.py
```

3. The system will:
   - Analyze vendor documents
   - Detect risk signals
   - Generate a risk score and recommendations

## Project Structure

```
vendor_risk_analyzer/
├── agents/
│   ├── document_analysis_agent.py
│   ├── risk_signal_agent.py
│   └── credibility_agent.py
├── config.py
├── main.py
├── requirements.txt
└── README.md
```

## Configuration

The system can be configured through `config.py`:
- Risk thresholds
- Required document fields
- Risk signal weights
- Vector store settings

## Requirements

- Python 3.8+
- OpenAI API key
- PDF processing capabilities
- Sufficient storage for document vectorization

## Note

This system requires proper document formatting and access to vendor information. Ensure all documents are properly formatted and contain the necessary information for analysis. 