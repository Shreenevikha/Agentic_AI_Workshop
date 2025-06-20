import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Switch,
  FormControlLabel,
  TextField,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Alert,
  useTheme
} from '@mui/material';
import {
  Settings,
  Notifications,
  Security,
  Storage,
  Api,
  Save,
  Refresh,
  CheckCircle,
  Warning,
  Info
} from '@mui/icons-material';

const SettingsPage = () => {
  const theme = useTheme();
  const [settings, setSettings] = useState({
    notifications: {
      email: true,
      push: false,
      complianceAlerts: true,
      systemUpdates: true
    },
    security: {
      twoFactorAuth: false,
      sessionTimeout: 30,
      autoLogout: true
    },
    system: {
      autoBackup: true,
      dataRetention: 365,
      maxFileSize: 10,
      enableAnalytics: true
    },
    api: {
      geminiApiKey: 'sk-...',
      maxTokens: 4000,
      temperature: 0.7
    }
  });

  const [saved, setSaved] = useState(false);

  const handleSettingChange = (category, setting, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [setting]: value
      }
    }));
    setSaved(false);
  };

  const handleSave = () => {
    // Simulate saving settings
    setTimeout(() => {
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    }, 1000);
  };

  const systemStatus = {
    database: { status: 'online', message: 'MongoDB connection stable' },
    vectorStore: { status: 'online', message: 'ChromaDB running normally' },
    aiModel: { status: 'online', message: 'Gemini API accessible' },
    storage: { status: 'warning', message: 'Storage at 75% capacity' }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'online':
        return <CheckCircle color="success" />;
      case 'warning':
        return <Warning color="warning" />;
      case 'error':
        return <Warning color="error" />;
      default:
        return <Info color="info" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'online':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Configure system preferences and user settings
      </Typography>

      {saved && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Settings saved successfully!
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Notifications Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="Notifications"
              avatar={<Notifications />}
            />
            <CardContent>
              <List>
                <ListItem>
                  <ListItemText
                    primary="Email Notifications"
                    secondary="Receive compliance alerts via email"
                  />
                  <Switch
                    checked={settings.notifications.email}
                    onChange={(e) => handleSettingChange('notifications', 'email', e.target.checked)}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Push Notifications"
                    secondary="Browser push notifications"
                  />
                  <Switch
                    checked={settings.notifications.push}
                    onChange={(e) => handleSettingChange('notifications', 'push', e.target.checked)}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Compliance Alerts"
                    secondary="Immediate alerts for compliance issues"
                  />
                  <Switch
                    checked={settings.notifications.complianceAlerts}
                    onChange={(e) => handleSettingChange('notifications', 'complianceAlerts', e.target.checked)}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="System Updates"
                    secondary="Notifications about system maintenance"
                  />
                  <Switch
                    checked={settings.notifications.systemUpdates}
                    onChange={(e) => handleSettingChange('notifications', 'systemUpdates', e.target.checked)}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Security Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="Security"
              avatar={<Security />}
            />
            <CardContent>
              <List>
                <ListItem>
                  <ListItemText
                    primary="Two-Factor Authentication"
                    secondary="Enhanced security with 2FA"
                  />
                  <Switch
                    checked={settings.security.twoFactorAuth}
                    onChange={(e) => handleSettingChange('security', 'twoFactorAuth', e.target.checked)}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Auto Logout"
                    secondary="Automatically log out after inactivity"
                  />
                  <Switch
                    checked={settings.security.autoLogout}
                    onChange={(e) => handleSettingChange('security', 'autoLogout', e.target.checked)}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Session Timeout (minutes)"
                    secondary="Inactive session timeout duration"
                  />
                  <TextField
                    type="number"
                    value={settings.security.sessionTimeout}
                    onChange={(e) => handleSettingChange('security', 'sessionTimeout', parseInt(e.target.value))}
                    size="small"
                    sx={{ width: 100 }}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* System Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="System"
              avatar={<Storage />}
            />
            <CardContent>
              <List>
                <ListItem>
                  <ListItemText
                    primary="Auto Backup"
                    secondary="Automatically backup data daily"
                  />
                  <Switch
                    checked={settings.system.autoBackup}
                    onChange={(e) => handleSettingChange('system', 'autoBackup', e.target.checked)}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Data Retention (days)"
                    secondary="How long to keep backup data"
                  />
                  <TextField
                    type="number"
                    value={settings.system.dataRetention}
                    onChange={(e) => handleSettingChange('system', 'dataRetention', parseInt(e.target.value))}
                    size="small"
                    sx={{ width: 100 }}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Max File Size (MB)"
                    secondary="Maximum file size for uploads"
                  />
                  <TextField
                    type="number"
                    value={settings.system.maxFileSize}
                    onChange={(e) => handleSettingChange('system', 'maxFileSize', parseInt(e.target.value))}
                    size="small"
                    sx={{ width: 100 }}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Analytics"
                    secondary="Enable usage analytics and reporting"
                  />
                  <Switch
                    checked={settings.system.enableAnalytics}
                    onChange={(e) => handleSettingChange('system', 'enableAnalytics', e.target.checked)}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* API Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="AI Configuration"
              avatar={<Api />}
            />
            <CardContent>
              <List>
                <ListItem>
                  <ListItemText
                    primary="Gemini API Key"
                    secondary="API key for AI model access"
                  />
                  <TextField
                    type="password"
                    value={settings.api.geminiApiKey}
                    onChange={(e) => handleSettingChange('api', 'geminiApiKey', e.target.value)}
                    size="small"
                    sx={{ width: 200 }}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Max Tokens"
                    secondary="Maximum tokens per AI request"
                  />
                  <TextField
                    type="number"
                    value={settings.api.maxTokens}
                    onChange={(e) => handleSettingChange('api', 'maxTokens', parseInt(e.target.value))}
                    size="small"
                    sx={{ width: 100 }}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Temperature"
                    secondary="AI response creativity (0.0-1.0)"
                  />
                  <TextField
                    type="number"
                    inputProps={{ step: 0.1, min: 0, max: 1 }}
                    value={settings.api.temperature}
                    onChange={(e) => handleSettingChange('api', 'temperature', parseFloat(e.target.value))}
                    size="small"
                    sx={{ width: 100 }}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* System Status */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              title="System Status"
              avatar={<Settings />}
            />
            <CardContent>
              <Grid container spacing={2}>
                {Object.entries(systemStatus).map(([service, status]) => (
                  <Grid item xs={12} sm={6} md={3} key={service}>
                    <Box sx={{ 
                      p: 2, 
                      border: 1, 
                      borderColor: 'divider', 
                      borderRadius: 1,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1
                    }}>
                      {getStatusIcon(status.status)}
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="subtitle2" sx={{ textTransform: 'capitalize' }}>
                          {service}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {status.message}
                        </Typography>
                      </Box>
                      <Chip
                        label={status.status}
                        color={getStatusColor(status.status)}
                        size="small"
                      />
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Action Buttons */}
      <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={() => window.location.reload()}
        >
          Reset to Defaults
        </Button>
        <Button
          variant="contained"
          startIcon={<Save />}
          onClick={handleSave}
        >
          Save Settings
        </Button>
      </Box>
    </Box>
  );
};

export default SettingsPage; 