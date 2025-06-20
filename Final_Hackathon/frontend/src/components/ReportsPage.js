import React, { useState } from 'react';
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
  useTheme
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
  Info
} from '@mui/icons-material';

const ReportsPage = () => {
  const theme = useTheme();
  const [selectedReport, setSelectedReport] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const mockReports = [
    {
      id: 1,
      title: 'Monthly Compliance Report',
      type: 'compliance',
      date: '2024-01-31',
      status: 'completed',
      summary: {
        totalTransactions: 1250,
        compliantRate: 94.4,
        flaggedIssues: 5,
        riskScore: 3.2
      },
      fileSize: '2.3 MB',
      description: 'Comprehensive monthly compliance analysis for January 2024'
    },
    {
      id: 2,
      title: 'Tax Filing Summary',
      type: 'tax',
      date: '2024-01-15',
      status: 'completed',
      summary: {
        totalAmount: 125000,
        deductions: 15000,
        taxableIncome: 110000,
        estimatedTax: 22000
      },
      fileSize: '1.8 MB',
      description: 'Tax filing preparation summary with calculations'
    },
    {
      id: 3,
      title: 'Anomaly Detection Report',
      type: 'anomaly',
      date: '2024-01-20',
      status: 'completed',
      summary: {
        anomaliesDetected: 12,
        highRisk: 3,
        mediumRisk: 6,
        lowRisk: 3
      },
      fileSize: '1.2 MB',
      description: 'AI-powered anomaly detection results'
    },
    {
      id: 4,
      title: 'Regulatory Update Report',
      type: 'regulatory',
      date: '2024-01-25',
      status: 'completed',
      summary: {
        newRegulations: 8,
        updatedRegulations: 15,
        affectedTransactions: 45
      },
      fileSize: '0.9 MB',
      description: 'Latest regulatory changes and their impact'
    }
  ];

  const getReportIcon = (type) => {
    switch (type) {
      case 'compliance':
        return <Assessment color="primary" />;
      case 'tax':
        return <Description color="success" />;
      case 'anomaly':
        return <TrendingDown color="warning" />;
      case 'regulatory':
        return <TrendingUp color="info" />;
      default:
        return <Description />;
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'processing':
        return <Warning color="warning" />;
      case 'failed':
        return <Error color="error" />;
      default:
        return <Info />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const handleViewReport = (report) => {
    setSelectedReport(report);
    setDialogOpen(true);
  };

  const handleDownloadReport = (report) => {
    // Simulate download
    console.log(`Downloading report: ${report.title}`);
    // In a real app, this would trigger a file download
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
        Reports
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        View and download generated compliance and tax reports
      </Typography>

      <Grid container spacing={3}>
        {mockReports.map((report) => (
          <Grid item xs={12} md={6} lg={4} key={report.id}>
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
                  {getReportIcon(report.type)}
                  <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
                    {report.title}
                  </Typography>
                  <Chip
                    icon={getStatusIcon(report.status)}
                    label={report.status}
                    color={getStatusColor(report.status)}
                    size="small"
                  />
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {report.description}
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CalendarToday sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
                  <Typography variant="body2" color="text.secondary">
                    {new Date(report.date).toLocaleDateString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
                    {report.fileSize}
                  </Typography>
                </Box>

                {/* Summary Stats */}
                <Box sx={{ mt: 2 }}>
                  {report.type === 'compliance' && (
                    <Grid container spacing={1}>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          Transactions
                        </Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {report.summary.totalTransactions}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          Compliance Rate
                        </Typography>
                        <Typography variant="body2" fontWeight="bold" color="success.main">
                          {report.summary.compliantRate}%
                        </Typography>
                      </Grid>
                    </Grid>
                  )}

                  {report.type === 'tax' && (
                    <Grid container spacing={1}>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          Total Amount
                        </Typography>
                        <Typography variant="body2" fontWeight="bold">
                          ${report.summary.totalAmount.toLocaleString()}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          Estimated Tax
                        </Typography>
                        <Typography variant="body2" fontWeight="bold" color="warning.main">
                          ${report.summary.estimatedTax.toLocaleString()}
                        </Typography>
                      </Grid>
                    </Grid>
                  )}

                  {report.type === 'anomaly' && (
                    <Grid container spacing={1}>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          Anomalies
                        </Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {report.summary.anomaliesDetected}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          High Risk
                        </Typography>
                        <Typography variant="body2" fontWeight="bold" color="error.main">
                          {report.summary.highRisk}
                        </Typography>
                      </Grid>
                    </Grid>
                  )}

                  {report.type === 'regulatory' && (
                    <Grid container spacing={1}>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          New Regulations
                        </Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {report.summary.newRegulations}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          Affected TXNs
                        </Typography>
                        <Typography variant="body2" fontWeight="bold" color="warning.main">
                          {report.summary.affectedTransactions}
                        </Typography>
                      </Grid>
                    </Grid>
                  )}
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
                <Button
                  size="small"
                  startIcon={<Download />}
                  onClick={() => handleDownloadReport(report)}
                >
                  Download
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Report Details Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedReport?.title}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            {selectedReport?.description}
          </Typography>
          
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Report Details
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Generated Date
                </Typography>
                <Typography variant="body1">
                  {selectedReport?.date}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  File Size
                </Typography>
                <Typography variant="body1">
                  {selectedReport?.fileSize}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Status
                </Typography>
                <Chip
                  icon={getStatusIcon(selectedReport?.status)}
                  label={selectedReport?.status}
                  color={getStatusColor(selectedReport?.status)}
                  size="small"
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            Close
          </Button>
          <Button
            variant="contained"
            startIcon={<Download />}
            onClick={() => handleDownloadReport(selectedReport)}
          >
            Download Report
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ReportsPage; 