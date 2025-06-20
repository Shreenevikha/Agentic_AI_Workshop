#SHREENEVIKHA N
# Agentic AI-Based Autonomous Compliance Checker & Tax Filing Assistant


Documentation Link: https://docs.google.com/document/d/1NSuaKAhlBKar_injYquNsVDMOY6yMKC2UjgG8MDMmC4/edit?usp=sharing

Workflow Link : https://www.mermaidchart.com/app/projects/fb0e2671-610e-4e29-8e52-07fd7a80f667/diagrams/f734ef4c-f54f-4bea-ba3d-5d6dd43e92e4/version/v0.1/edit


This project is a sophisticated, AI-driven platform designed to automate the complex process of financial compliance and tax filing. It leverages a multi-agent system to ingest raw financial data, validate it against regulations, detect anomalies, and generate filing-ready reports, all accessible through a modern web interface.

## Core Architecture

The application is built on a modern, decoupled architecture:

*   **Frontend:** A responsive user interface built with **React** and **Material-UI**, allowing users to upload files and visualize compliance results on an interactive dashboard.
*   **Backend:** A powerful and scalable API built with **Python FastAPI**. This backend orchestrates the entire AI pipeline.
*   **AI Agents:** The core logic is powered by a series of specialized AI agents built with **Google's Gemini** models. Each agent has a specific role in the compliance workflow.
*   **Database:** **MongoDB** is used for storing transaction data, regulations, and generated reports, providing flexibility and scalability.

---

## Project Flow: The 5-Agent Compliance Pipeline

The heart of this application is the autonomous pipeline that runs when a user uploads a file. Here is a step-by-step breakdown of the data flow:

### 1. **File Upload (Frontend)**
*   A user visits the "Upload" page and drops a CSV file containing their financial transactions.
*   Upon clicking "Upload & Run," the React frontend sends the file to the backend.

### 2. **Pipeline Kick-off (Backend)**
*   The FastAPI backend receives the file at the `/api/v1/pipeline/run` endpoint.
*   The system uses the `pandas` library for robust CSV parsing and **automatically detects the date range** from the data, making the process seamless for the user.

### 3. **Data Cleaning (Backend)**
*   Before the main pipeline begins, a **Data Sanitization** step runs. It finds and corrects any transactions in the database that may have been saved with an invalid status during previous runs, ensuring data integrity.

### 4. **The AI Agent Relay (Backend)**
The transactions are then passed sequentially through a relay of five specialized AI agents:

*   **Agent 1: Regulation Fetcher**
    *   **Role:** The Legal Expert.
    *   **Action:** It queries a vector database (ChromaDB) to retrieve the specific tax laws and regulations that are relevant to the user's business domain and filing type.

*   **Agent 2: Compliance Validator**
    *   **Role:** The Auditor.
    *   **Action:** It meticulously compares each individual transaction against the regulations provided by the Fetcher. It uses a powerful LLM prompt to classify each transaction as `'valid'`, `'invalid'`, or `'pending'`.

*   **Agent 3: Filing Data Aggregator**
    *   **Role:** The Accountant.
    *   **Action:** It takes the validated transactions and aggregates them into structured summaries, calculating total taxable values and preparing the data for reporting.

*   **Agent 4: Anomaly Detector**
    *   **Role:** The Fraud Investigator.
    *   **Action:** It scans the entire dataset for suspicious patterns that might indicate errors or fraud, such as duplicate transactions, unusually high amounts, or future dates.

*   **Agent 5: Filing Report Generator**
    *   **Role:** The Administrative Assistant.
    *   **Action:** It takes the clean, aggregated data and generates the final output, including a human-readable summary and a machine-readable JSON file.

### 5. **Consolidated Response (Backend)**
*   The pipeline API gathers the results from all five agents—the compliance summary, flagged entries, filing readiness level, and detected anomalies—into a single, clean JSON object.

### 6. **Redirect and Display (Frontend)**
*   The React frontend receives the successful response from the backend.
*   It immediately redirects the user to the **Dashboard** page, passing the entire results object in the navigation state.

### 7. **Dashboard Visualization (Frontend)**
*   The Dashboard component receives the data and renders it into a series of user-friendly cards and tables, giving the user a complete overview of their compliance status.

---

## How to Run This Project

### Prerequisites
*   Python 3.8+
*   Node.js and npm
*   MongoDB instance

### Backend Setup
1.  Navigate to the `Final_Hackathon/backend` directory.
2.  Create a virtual environment: `python -m venv venv`
3.  Activate it: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
4.  Install dependencies: `pip install -r requirements.txt`
5.  Create a `.env` file from `.env.example` and add your `GOOGLE_API_KEY` and `MONGO_URI`.
6.  Run the server: `uvicorn main:app --reload`

### Frontend Setup
1.  Navigate to the `Final_Hackathon/frontend` directory.
2.  Install dependencies: `npm install`
3.  Start the development server: `npm start`
4.  Open your browser to `http://localhost:3000`.

## Project Structure
```
Final_Hackathon/
├── backend/
│   ├── agents/
│   ├── api/
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── services/
│   └── utils/
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── docs/
└── README.md
```

## Environment Setup

### Backend Environment Variables (.env)
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/tax_compliance

# Vector Database
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=tax-regulations

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Security
SECRET_KEY=your_secret_key
JWT_SECRET=your_jwt_secret

# External APIs
GOVERNMENT_API_KEY=your_government_api_key
TAX_PORTAL_API_URL=https://api.taxportal.gov.in
```

### Frontend Environment Variables (.env)
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
```

## Installation & Setup

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## API Endpoints

### Regulation Fetcher Agent
- `POST /api/v1/regulations/fetch` - Fetch regulations by domain
- `GET /api/v1/regulations/sync` - Sync latest regulations
- `GET /api/v1/regulations/search` - Search regulations

### Compliance Validator Agent
- `POST /api/v1/compliance/validate` - Validate transactions
- `GET /api/v1/compliance/status` - Get validation status

### Filing Data Aggregator Agent
- `POST /api/v1/filing/aggregate` - Aggregate filing data
- `GET /api/v1/filing/status` - Get aggregation status

### Anomaly Detector Agent
- `POST /api/v1/anomaly/detect` - Detect anomalies
- `GET /api/v1/anomaly/report` - Get anomaly report

### Filing Report Generator Agent
- `POST /api/v1/reports/generate` - Generate reports
- `GET /api/v1/reports/download/{report_id}` - Download report

## Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Deployment
- Backend: Docker container with FastAPI
- Frontend: Build optimized React app
- Database: PostgreSQL with vector extensions

## Security Considerations
- API key management
- Data encryption at rest
- Secure file uploads
- Rate limiting
- Input validation

## Contributing
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License
MIT License 