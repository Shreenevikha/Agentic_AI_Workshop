# Vendor Risk Analyzer

An AI-powered backend system for evaluating vendor credibility and compliance risk using Agentic AI, RAG, LangChain, and LangGraph.

## Project Goals
- Empower finance and procurement teams to identify vendor risks early.
- Use AI agents to autonomously analyze documents, detect red flags, fetch external compliance data, and generate a final risk score.
- Integrate RAG to enrich agent reasoning with external knowledge.
- Structure agent interactions and decision-making using LangGraph flows.

## Architecture

- **Document Analysis Agent**: Extracts key risk indicators from vendor documents.
- **Risk Signal Detection Agent**: Detects anomalies and risk flags in extracted data.
- **External Intelligence Agent (RAG)**: Uses vector DB and retriever pipeline to fetch external compliance data.
- **Credibility Scoring Agent**: Aggregates all insights to generate a risk score and justification.
- **LangGraph Flow**: Orchestrates agent workflow and data passing.

## Folder Structure
```
vendor_risk_analyzer/
  agents/
    document_analysis_agent.py
    risk_signal_agent.py
    external_intelligence_agent.py
    credibility_scoring_agent.py
  data/
  retriever/
    vector_store.py
    retriever_pipeline.py
  flows/
    vendor_risk_flow.py
  main.py
  config.py
  requirements.txt
  README.md
```

## Setup
1. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On Unix
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Add your OpenAI API key to a `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage
1. Place vendor documents in the `data/` directory.
2. Run the analyzer:
   ```bash
   python main.py
   ```
3. The system will:
   - Analyze documents
   - Detect risk signals
   - Fetch external intelligence
   - Generate a risk score and justification

## Requirements
- Python 3.8+
- OpenAI API key
- PDF/text documents for analysis

## Output
- Risk score and justification for each vendor
- Detailed report of detected risks and external findings 