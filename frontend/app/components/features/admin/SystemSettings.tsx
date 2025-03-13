'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Grid,
  Switch,
  FormControlLabel,
  Divider,
  Slider,
  InputAdornment,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { z } from 'zod';

interface SystemSettings {
  companyName: string;
  maxConcurrentStreams: number;
  retentionPeriodDays: number;
  enableAuditLog: boolean;
  enableNotifications: boolean;
  notificationEmail: string;
  apiRateLimit: number;
  storageQuotaGB: number;
  backupEnabled: boolean;
  backupFrequencyHours: number;
}

const settingsSchema = z.object({
  companyName: z.string().min(2, 'Company name must be at least 2 characters'),
  maxConcurrentStreams: z.number().min(1).max(50),
  retentionPeriodDays: z.number().min(1).max(365),
  enableAuditLog: z.boolean(),
  enableNotifications: z.boolean(),
  notificationEmail: z.string().email('Invalid email format'),
  apiRateLimit: z.number().min(10).max(1000),
  storageQuotaGB: z.number().min(1),
  backupEnabled: z.boolean(),
  backupFrequencyHours: z.number().min(1).max(168),
});

export function SystemSettings() {
  const [settings, setSettings] = useState<SystemSettings>({
    companyName: '',
    maxConcurrentStreams: 10,
    retentionPeriodDays: 30,
    enableAuditLog: true,
    enableNotifications: true,
    notificationEmail: '',
    apiRateLimit: 100,
    storageQuotaGB: 500,
    backupEnabled: true,
    backupFrequencyHours: 24,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/settings');
      if (!response.ok) throw new Error('Failed to fetch settings');
      const data = await response.json();
      setSettings(data);
    } catch (err) {
      setError('Failed to load settings. Please try again.');
      console.error('Settings fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const validateSettings = () => {
    try {
      settingsSchema.parse(settings);
      setValidationErrors({});
      return true;
    } catch (err) {
      if (err instanceof z.ZodError) {
        const errors: {[key: string]: string} = {};
        err.errors.forEach((error) => {
          if (error.path) {
            errors[error.path[0]] = error.message;
          }
        });
        setValidationErrors(errors);
      }
      return false;
    }
  };

  const handleSave = async () => {
    if (!validateSettings()) return;

    try {
      setSaving(true);
      const response = await fetch('/api/admin/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (!response.ok) throw new Error('Failed to save settings');

      setSuccess('Settings saved successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to save settings. Please try again.');
      console.error('Settings save error:', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5" component="h2">
          System Settings
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            startIcon={<RefreshIcon />}
            onClick={fetchSettings}
            disabled={saving}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      <Paper sx={{ p: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              General Settings
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Company Name"
              value={settings.companyName}
              onChange={(e) => setSettings({ ...settings, companyName: e.target.value })}
              error={!!validationErrors.companyName}
              helperText={validationErrors.companyName}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Notification Email"
              value={settings.notificationEmail}
              onChange={(e) => setSettings({ ...settings, notificationEmail: e.target.value })}
              error={!!validationErrors.notificationEmail}
              helperText={validationErrors.notificationEmail}
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Performance Settings
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography gutterBottom>
              Max Concurrent Streams
              <Tooltip title="Maximum number of camera streams that can be processed simultaneously">
                <IconButton size="small" sx={{ ml: 1 }}>
                  <InfoIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Typography>
            <Slider
              value={settings.maxConcurrentStreams}
              onChange={(_, value) => setSettings({ ...settings, maxConcurrentStreams: value as number })}
              min={1}
              max={50}
              marks
              valueLabelDisplay="auto"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography gutterBottom>
              API Rate Limit (requests/minute)
              <Tooltip title="Maximum number of API requests allowed per minute">
                <IconButton size="small" sx={{ ml: 1 }}>
                  <InfoIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Typography>
            <Slider
              value={settings.apiRateLimit}
              onChange={(_, value) => setSettings({ ...settings, apiRateLimit: value as number })}
              min={10}
              max={1000}
              step={10}
              marks
              valueLabelDisplay="auto"
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Storage Settings
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Storage Quota (GB)"
              value={settings.storageQuotaGB}
              onChange={(e) => setSettings({ ...settings, storageQuotaGB: Number(e.target.value) })}
              error={!!validationErrors.storageQuotaGB}
              helperText={validationErrors.storageQuotaGB}
              InputProps={{
                endAdornment: <InputAdornment position="end">GB</InputAdornment>,
              }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Data Retention Period"
              value={settings.retentionPeriodDays}
              onChange={(e) => setSettings({ ...settings, retentionPeriodDays: Number(e.target.value) })}
              error={!!validationErrors.retentionPeriodDays}
              helperText={validationErrors.retentionPeriodDays}
              InputProps={{
                endAdornment: <InputAdornment position="end">days</InputAdornment>,
              }}
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              System Features
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.enableAuditLog}
                  onChange={(e) => setSettings({ ...settings, enableAuditLog: e.target.checked })}
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  Audit Logging
                  <Tooltip title="Track all system actions and user activities">
                    <IconButton size="small" sx={{ ml: 1 }}>
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              }
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.enableNotifications}
                  onChange={(e) => setSettings({ ...settings, enableNotifications: e.target.checked })}
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  Email Notifications
                  <Tooltip title="Send email notifications for important events">
                    <IconButton size="small" sx={{ ml: 1 }}>
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              }
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Backup Configuration
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.backupEnabled}
                  onChange={(e) => setSettings({ ...settings, backupEnabled: e.target.checked })}
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  Automated Backups
                  <Tooltip title="Enable automated system backups">
                    <IconButton size="small" sx={{ ml: 1 }}>
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              }
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Backup Frequency"
              value={settings.backupFrequencyHours}
              onChange={(e) => setSettings({ ...settings, backupFrequencyHours: Number(e.target.value) })}
              error={!!validationErrors.backupFrequencyHours}
              helperText={validationErrors.backupFrequencyHours}
              disabled={!settings.backupEnabled}
              InputProps={{
                endAdornment: <InputAdornment position="end">hours</InputAdornment>,
              }}
            />
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
} 