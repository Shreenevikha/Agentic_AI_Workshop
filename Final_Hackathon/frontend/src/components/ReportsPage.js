import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  useTheme,
  CircularProgress,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Description,
  Download,
  Visibility,
  CalendarToday,
  Assessment,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  Error,
  Warning,
  Info,
  PictureAsPdf,
  Code,
  Refresh
} from '@mui/icons-material';
import { apiRequest, getApiUrl } from '../config/api';

const ReportsPage = () => {
  const theme = useTheme();
  const [reports, setReports] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  useEffect(() => {
    fetchReports();
    fetchSummary();
  }, []);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const response = await apiRequest('/reports/list');
      if (response.success) {
        setReports(response.reports);
      } else {
        setSnackbar({ open: true, message: 'Failed to fetch reports', severity: 'error' });
      }
    } catch (error) {
      console.error('Error fetching reports:', error);
      setSnackbar({ open: true, message: 'Error fetching reports', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await apiRequest('/reports/summary');
      if (response.success) {
        setSummary(response.summary);
      }
    } catch (error) {
      console.error('Error fetching summary:', error);
    }
  };

  const handleViewReport = (report) => {
    setSelectedReport(report);
    setDialogOpen(true);
  };

  const handleDownloadReport = async (report, fileType) => {
    try {
      const url = getApiUrl(`/reports/download/${report.report_id}?file_type=${fileType}`);
      
      // For file downloads, we need to use fetch directly
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Create download link
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', `${report.filing_type}_${report.report_id}.${fileType}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
      
      setSnackbar({ open: true, message: `${fileType.toUpperCase()} report downloaded successfully`, severity: 'success' });
    } catch (error) {
      console.error(`Error downloading ${fileType} report:`, error);
      setSnackbar({ open: true, message: `Failed to download ${fileType.toUpperCase()} report`, severity: 'error' });
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'ready':
      case 'completed':
        return 'success';
      case 'processing':
      case 'pending':
        return 'warning';
      case 'failed':
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'ready':
      case 'completed':
        return <CheckCircle color="success" />;
      case 'processing':
      case 'pending':
        return <Warning color="warning" />;
      case 'failed':
      case 'error':
        return <Error color="error" />;
      default:
        return <Info />;
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
            Reports
          </Typography>
          <Typography variant="body1" color="text.secondary">
            View and download generated compliance and tax reports
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchReports}
        >
          Refresh
        </Button>
      </Box>

      {/* Summary Cards */}
      {summary && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h4" color="primary" sx={{ fontWeight: 600 }}>
                {summary.total_reports}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Reports
              </Typography>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h4" color="success.main" sx={{ fontWeight: 600 }}>
                {summary.ready_reports + summary.submitted_reports}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Completed
              </Typography>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h4" color="warning.main" sx={{ fontWeight: 600 }}>
                {formatCurrency(summary.total_amount)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Amount
              </Typography>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h4" color="info.main" sx={{ fontWeight: 600 }}>
                {formatCurrency(summary.total_tax)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Tax
              </Typography>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Reports Grid */}
      <Grid container spacing={3}>
        {reports.length === 0 ? (
          <Grid item xs={12}>
            <Card sx={{ textAlign: 'center', p: 4 }}>
              <Description sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No Reports Available
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Generate your first report by uploading transaction data
              </Typography>
            </Card>
          </Grid>
        ) : (
          reports.map((report) => (
            <Grid item xs={12} md={6} lg={4} key={report.report_id}>
              <Card 
                sx={{ 
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'transform 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: theme.shadows[8]
                  }
                }}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Description color="primary" />
                    <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
                      {report.filing_type}
                    </Typography>
                    <Chip
                      icon={getStatusIcon(report.status)}
                      label={report.status}
                      color={getStatusColor(report.status)}
                      size="small"
                    />
                  </Box>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Report ID: {report.report_id}
                  </Typography>

                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <CalendarToday sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                      {formatDate(report.created_at)}
                    </Typography>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Total Amount: {formatCurrency(report.total_amount)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Tax Amount: {formatCurrency(report.tax_amount)}
                    </Typography>
                  </Box>
                </CardContent>

                <CardActions sx={{ justifyContent: 'space-between', p: 2 }}>
                  <Button
                    size="small"
                    startIcon={<Visibility />}
                    onClick={() => handleViewReport(report)}
                  >
                    View
                  </Button>
                  <Box>
                    <IconButton
                      size="small"
                      onClick={() => handleDownloadReport(report, 'pdf')}
                      title="Download PDF"
                    >
                      <PictureAsPdf />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDownloadReport(report, 'json')}
                      title="Download JSON"
                    >
                      <Code />
                    </IconButton>
                  </Box>
                </CardActions>
              </Card>
            </Grid>
          ))
        )}
      </Grid>

      {/* Report Detail Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Description sx={{ mr: 1 }} />
            Report Details
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedReport && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedReport.filing_type}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Report ID: {selectedReport.report_id}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Created: {formatDate(selectedReport.created_at)}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Status: {selectedReport.status}
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Financial Summary
              </Typography>
              <Typography variant="body2" gutterBottom>
                Total Amount: {formatCurrency(selectedReport.total_amount)}
              </Typography>
              <Typography variant="body2" gutterBottom>
                Tax Amount: {formatCurrency(selectedReport.tax_amount)}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
          <Button
            variant="contained"
            startIcon={<Download />}
            onClick={() => {
              handleDownloadReport(selectedReport, 'pdf');
              setDialogOpen(false);
            }}
          >
            Download PDF
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ReportsPage; 