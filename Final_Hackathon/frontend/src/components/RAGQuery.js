import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper,
} from '@mui/material';
import { ExpandMore, Search, QuestionAnswer, Psychology } from '@mui/icons-material';
import axios from 'axios';
import { getApiUrl } from '../config/api';

const RAGQuery = () => {
  const [query, setQuery] = useState('');
  const [domain, setDomain] = useState('');
  const [entityType, setEntityType] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const sampleDomains = ['GST', 'TDS', 'VAT', 'Income Tax'];
  const sampleEntityTypes = ['Company', 'Individual', 'Partnership', 'LLP'];

  const handleRAGQuery = async () => {
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await axios.post(getApiUrl('/api/v1/rag/query'), {
        query: query,
        domain: domain || undefined,
        entity_type: entityType || undefined,
      });

      if (response.data.success) {
        setResult(response.data);
        setSuccess('RAG query completed successfully!');
      } else {
        setError(response.data.error || 'Failed to process RAG query');
      }
    } catch (err) {
      console.error('Error in RAG query:', err);
      setError(err.response?.data?.detail || 'Failed to process RAG query');
    } finally {
      setLoading(false);
    }
  };

  const handleHybridSearch = async () => {
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await axios.post(getApiUrl('/api/v1/rag/hybrid-search'), {
        query: query,
        domain: domain || undefined,
        entity_type: entityType || undefined,
      });

      if (response.data.success) {
        setResult(response.data);
        setSuccess('Hybrid search completed successfully!');
      } else {
        setError(response.data.error || 'Failed to perform hybrid search');
      }
    } catch (err) {
      console.error('Error in hybrid search:', err);
      setError(err.response?.data?.detail || 'Failed to perform hybrid search');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        RAG Compliance Query
      </Typography>

      {/* Query Form */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Ask Tax Compliance Questions
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Enter your compliance question"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                multiline
                rows={3}
                placeholder="e.g., What are the GST registration requirements for companies?"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Domain (Optional)</InputLabel>
                <Select
                  value={domain}
                  label="Domain (Optional)"
                  onChange={(e) => setDomain(e.target.value)}
                >
                  {sampleDomains.map((d) => (
                    <MenuItem key={d} value={d}>
                      {d}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Entity Type (Optional)</InputLabel>
                <Select
                  value={entityType}
                  label="Entity Type (Optional)"
                  onChange={(e) => setEntityType(e.target.value)}
                >
                  {sampleEntityTypes.map((et) => (
                    <MenuItem key={et} value={et}>
                      {et}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Button
                variant="contained"
                startIcon={<QuestionAnswer />}
                onClick={handleRAGQuery}
                disabled={loading || !query.trim()}
                fullWidth
              >
                {loading ? <CircularProgress size={20} /> : 'Ask RAG Query'}
              </Button>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Button
                variant="outlined"
                startIcon={<Search />}
                onClick={handleHybridSearch}
                disabled={loading || !query.trim()}
                fullWidth
              >
                {loading ? <CircularProgress size={20} /> : 'Hybrid Search'}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Results */}
      {result && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Results
          </Typography>
          
          {/* RAG Answer */}
          {result.answer && (
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  AI Answer
                </Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {result.answer}
                </Typography>
              </CardContent>
            </Card>
          )}

          {/* Sources */}
          {result.sources && result.sources.length > 0 && (
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Sources Used ({result.sources.length})
                </Typography>
                {result.sources.map((source, index) => (
                  <Accordion key={index} sx={{ mb: 1 }}>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2">
                          Source {index + 1}
                        </Typography>
                        {source.metadata && (
                          <Chip
                            label={source.metadata.get('domain', 'Unknown')}
                            size="small"
                            color="primary"
                          />
                        )}
                        {source.score && (
                          <Chip
                            label={`Score: ${source.score.toFixed(2)}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {source.content}
                      </Typography>
                    </AccordionDetails>
                  </Accordion>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Search Results */}
          {result.results && result.results.length > 0 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Search Results ({result.count})
                </Typography>
                {result.results.map((item, index) => (
                  <Paper key={index} sx={{ p: 2, mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Typography variant="subtitle1">
                        Result {index + 1}
                      </Typography>
                      <Box>
                        <Chip
                          label={item.source}
                          size="small"
                          color={item.source === 'vector_search' ? 'primary' : 'secondary'}
                          sx={{ mr: 1 }}
                        />
                        {item.score && (
                          <Chip
                            label={`Score: ${item.score.toFixed(2)}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {item.content}
                    </Typography>
                  </Paper>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Execution Info */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Execution ID: {result.execution_id}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Empty State */}
      {!loading && !result && !error && (
        <Card>
          <CardContent>
            <Typography variant="body1" color="text.secondary" align="center">
              Enter a compliance question to get AI-powered answers using RAG
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default RAGQuery; 