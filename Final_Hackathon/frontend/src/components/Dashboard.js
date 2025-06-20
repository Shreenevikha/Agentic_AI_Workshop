import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert
} from '@mui/material';

// Helper function to format currency
const formatToRupees = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
  }).format(amount);
};

const Dashboard = () => {
  const location = useLocation();
  const [dashboardData, setDashboardData] = useState(null);

  useEffect(() => {
    if (location.state && location.state.dashboardData) {
      console.log("Received data on dashboard:", location.state.dashboardData);
      setDashboardData(location.state.dashboardData);
    }
  }, [location.state]);

  if (!dashboardData || !dashboardData.success) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>Dashboard</Typography>
        <Alert severity={dashboardData?.error ? "error" : "info"}>
          {dashboardData?.error 
            ? `Pipeline failed: ${dashboardData.error}`
            : "Please go to the 'Upload' page to upload a file and run the compliance pipeline."}
        </Alert>
      </Box>
    );
  }

  const { compliance_summary, filing_summary, flagged_entries, anomalies } = dashboardData;

  // Safely calculate readiness percentage
  const readinessPercentage = filing_summary?.readiness_level
    ? (filing_summary.readiness_level * 100).toFixed(2)
    : 0;

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 4 }}>Dashboard</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Compliance Summary</Typography>
              <Typography>Total Items: {compliance_summary.total_validated}</Typography>
              <Typography color="success.main">Valid: {compliance_summary.valid_count}</Typography>
              <Typography color="error.main">Invalid: {compliance_summary.invalid_count}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Filing Readiness</Typography>
              <Typography>Readiness: {readinessPercentage}%</Typography>
              <Typography>Total Taxable Value: {formatToRupees(filing_summary.total_taxable_value)}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6">Flagged Entries</Typography>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Transaction ID</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Details</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {flagged_entries.map((entry, idx) => (
                      <TableRow key={idx}>
                        <TableCell>{entry.transaction_id}</TableCell>
                        <TableCell>
                          <Chip label={entry.validation_result.status} color="error" size="small" />
                        </TableCell>
                        <TableCell>{entry.validation_result.details}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6">Anomalies Detected</Typography>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Type</TableCell>
                      <TableCell>Severity</TableCell>
                      <TableCell>Description</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {anomalies.map((anomaly, idx) => (
                      <TableRow key={idx}>
                        <TableCell>{anomaly.anomaly_type}</TableCell>
                        <TableCell>
                          <Chip
                            label={anomaly.severity}
                            color={anomaly.severity === 'HIGH' ? 'error' : 'warning'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{anomaly.description}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;