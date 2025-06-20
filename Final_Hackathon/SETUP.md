# Setup Guide - Tax Compliance AI Assistant

## Prerequisites

### 1. Python Environment
- Python 3.8+ installed
- pip package manager

### 2. Node.js Environment
- Node.js 16+ installed
- npm package manager

### 3. MongoDB
- MongoDB installed and running locally
- Or MongoDB Atlas cloud instance

### 4. Required API Keys
- **Google Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Pinecone API Key**: Get from [Pinecone Console](https://app.pinecone.io/)

## Backend Setup

### 1. Navigate to Backend Directory
```bash
cd Final_Hackathon/backend
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit .env file with your API keys
# Required variables:
# - GOOGLE_API_KEY=your_google_api_key_here
# - MONGODB_URL=mongodb://localhost:27017/tax_compliance
# - PINECONE_API_KEY=your_pinecone_api_key_here
# - PINECONE_ENVIRONMENT=your_pinecone_environment_here
```

### 5. Test Backend
```bash
# Test the Regulation Fetcher Agent
python test_regulation_agent.py

# Start the FastAPI server
python main.py
```

The backend will be available at: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

## Frontend Setup

### 1. Navigate to Frontend Directory
```bash
cd Final_Hackathon/frontend
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Start Development Server
```bash
npm start
```

The frontend will be available at: `http://localhost:3000`

## Testing the System

### 1. Backend Testing
```bash
cd backend
python test_regulation_agent.py
```

Expected output:
```
🚀 Testing Regulation Fetcher Agent...
✅ Connected to MongoDB
✅ Regulation Fetcher Agent initialized
📋 Test 1: Fetching regulations for GST domain...
✅ Successfully fetched 0 regulations
📊 Execution ID: [uuid]
📋 Test 2: Syncing sample regulations...
✅ Successfully synced 2 regulations
📊 Execution ID: [uuid]
📋 Test 3: Searching regulations...
✅ Found 0 search results
📋 Test 4: Fetching regulations after sync...
✅ Successfully fetched 2 regulations (including synced)
  - GST Registration Requirements (database)
  - TDS Compliance Rules (database)
🎉 All tests completed successfully!
✅ Database connection closed
```

### 2. Frontend Testing
1. Open `http://localhost:3000` in your browser
2. Navigate to "Regulations" tab
3. Select "GST" as domain and "Company" as entity type
4. Click "Fetch Regulations"
5. Try "Sync Sample Data" to add test regulations

### 3. API Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test fetch regulations
curl -X POST http://localhost:8000/api/v1/regulations/fetch \
  -H "Content-Type: application/json" \
  -d '{"domain": "GST", "entity_type": "Company"}'
```

## Troubleshooting

### Common Issues

#### 1. MongoDB Connection Error
```
Error: Failed to connect to MongoDB
```
**Solution**: Ensure MongoDB is running
```bash
# Start MongoDB (Windows)
net start MongoDB

# Start MongoDB (macOS/Linux)
sudo systemctl start mongod
```

#### 2. Pinecone API Error
```
Error: Failed to initialize Pinecone
```
**Solution**: Check your Pinecone API key and environment
- Verify API key is correct
- Ensure environment matches your Pinecone project

#### 3. Google API Error
```
Error: Invalid API key
```
**Solution**: Verify your Google Gemini API key
- Check key format and validity
- Ensure billing is enabled for the project

#### 4. Port Already in Use
```
Error: Address already in use
```
**Solution**: Change port in `.env` file
```env
API_PORT=8001
```

#### 5. Frontend Proxy Error
```
Error: Proxy error
```
**Solution**: Ensure backend is running on port 8000
- Check if `http://localhost:8000/health` returns 200
- Verify CORS settings in backend

## Environment Variables Reference

### Backend (.env)
```env
# Google Gemini Configuration
GOOGLE_API_KEY=your_google_api_key_here

# Database Configuration - MongoDB
MONGODB_URL=mongodb://localhost:27017/tax_compliance

# Vector Database (Pinecone)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
PINECONE_INDEX_NAME=tax-regulations

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Security
SECRET_KEY=your_secret_key_here_make_it_long_and_random
JWT_SECRET=your_jwt_secret_here_make_it_long_and_random

# External APIs
GOVERNMENT_API_KEY=your_government_api_key_here
TAX_PORTAL_API_URL=https://api.taxportal.gov.in

# Logging
LOG_LEVEL=INFO
```

### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
```

## Next Steps

After successful setup:

1. **Test the Regulation Fetcher Agent** - Verify RAG functionality
2. **Implement the next agent** - Compliance Validator Agent
3. **Add more test data** - Expand regulation database
4. **Enhance frontend** - Add more features and components
5. **Deploy to production** - Set up production environment

## Support

If you encounter issues:
1. Check the logs in the terminal
2. Verify all environment variables are set
3. Ensure all services are running
4. Check API documentation at `http://localhost:8000/docs` 