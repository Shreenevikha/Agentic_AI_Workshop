// API Configuration
const API_CONFIG = {
  // Backend base URL - change this for production
  BASE_URL: 'http://localhost:8000',
  
  // API endpoints
  ENDPOINTS: {
    HEALTH: '/health',
    PIPELINE: '/api/v1/pipeline/run',
    REGULATIONS: {
      FETCH: '/api/v1/regulations/fetch',
      SYNC: '/api/v1/regulations/sync'
    },
    RAG: {
      QUERY: '/api/v1/rag/query',
      HYBRID_SEARCH: '/api/v1/rag/hybrid-search'
    },
    COMPLIANCE: '/api/v1/compliance/validate',
    FILING: '/api/v1/filing/aggregate',
    ANOMALY: '/api/v1/anomaly/detect',
    REPORT: '/api/v1/report/generate'
  }
};

// Helper function to get full API URL
export const getApiUrl = (endpoint) => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

// Helper function to make API requests with error handling
export const apiRequest = async (endpoint, options = {}) => {
  const url = getApiUrl(endpoint);
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options
  };

  try {
    console.log(`Making API request to: ${url}`);
    const response = await fetch(url, defaultOptions);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API Error ${response.status}:`, errorText);
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
    const data = await response.json();
    console.log(`API Success:`, data);
    return data;
  } catch (error) {
    console.error('API Request failed:', error);
    throw error;
  }
};

export default API_CONFIG; 