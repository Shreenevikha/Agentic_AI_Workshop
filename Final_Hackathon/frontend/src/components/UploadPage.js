import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Alert,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Grid,
  Card,
  CardContent,
  Paper,
  IconButton
} from '@mui/material';
import { CloudUpload, Description, Delete, Upload } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { getApiUrl } from '../config/api';

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

const UploadPage = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const onDrop = (acceptedFiles) => {
    const csvFiles = acceptedFiles.filter(
      (file) => file.type === 'text/csv' || file.name.endsWith('.csv')
    );
    setFiles(csvFiles); // Replace instead of append for a single-file flow
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    multiple: false, // Ensure only one file is processed
  });

  const removeFile = () => {
    setFiles([]);
  };

  const handleUploadAndRun = async () => {
    if (files.length === 0) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', files[0]);
    formData.append('domain', 'tax');
    formData.append('entity_type', 'business');
    formData.append('filing_type', 'GSTR-1');
    formData.append('period_start', new Date(new Date().setMonth(new Date().getMonth() - 1)).toISOString());
    formData.append('period_end', new Date().toISOString());

    try {
      const apiUrl = getApiUrl('/api/v1/pipeline/run');
      console.log('Sending request to:', apiUrl);
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const result = await response.json();
      console.log('Response data:', result);

      if (!result.success) {
        throw new Error(result.error || 'Failed to process file and run pipeline.');
      }

      // Redirect to dashboard with the results
      navigate('/', { state: { dashboardData: result } });

    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Upload & Run Compliance Pipeline</Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Upload a single CSV file to automatically trigger the full compliance analysis.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Paper
            {...getRootProps()}
            sx={{
              p: 4,
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.400',
              textAlign: 'center',
              cursor: 'pointer',
              mb: 2,
            }}
          >
            <input {...getInputProps()} />
            <CloudUpload sx={{ fontSize: 48, color: 'primary.main' }} />
            <Typography>
              {isDragActive ? 'Drop your CSV file here' : 'Drag & drop a single CSV file, or click to select'}
            </Typography>
          </Paper>

          {files.length > 0 && (
             <Card sx={{ mb: 2 }}>
              <CardContent>
                 <List>
                  <ListItem
                    secondaryAction={
                      <IconButton edge="end" onClick={removeFile}>
                        <Delete />
                      </IconButton>
                    }
                  >
                    <ListItemIcon><Description /></ListItemIcon>
                    <ListItemText primary={files[0].name} secondary={formatFileSize(files[0].size)} />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          )}

          <Button
            variant="contained"
            startIcon={<Upload />}
            onClick={handleUploadAndRun}
            disabled={files.length === 0 || loading}
          >
            {loading ? 'Processing...' : 'Upload & Run'}
          </Button>

          {loading && <LinearProgress sx={{ mt: 2 }} />}
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        </Grid>

        <Grid item xs={12} md={5}>
          <Card>
            <CardContent>
              <Typography variant="h6">Instructions</Typography>
              <Typography variant="body2" component="div">
                <ul>
                  <li>Ensure your CSV has columns: `date`, `description`, `amount`.</li>
                  <li>Optional columns: `category`, `vendor`.</li>
                  <li>The pipeline will run automatically after upload.</li>
                  <li>You will be redirected to the dashboard to view the results.</li>
                </ul>
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default UploadPage; 