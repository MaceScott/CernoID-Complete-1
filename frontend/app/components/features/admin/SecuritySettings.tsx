'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Switch,
  FormControlLabel,
  Divider,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Tooltip,
  IconButton,
  Slider,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { z } from 'zod';

interface SecuritySettings {
  faceRecognitionEnabled: boolean;
  faceRecognitionThreshold: number;
  motionDetectionEnabled: boolean;
  motionSensitivity: number;
  twoFactorAuthRequired: boolean;
  passwordPolicy: {
    minLength: number;
    requireUppercase: boolean;
    requireNumbers: boolean;
    requireSpecialChars: boolean;
    expiryDays: number;
  };
  sessionTimeout: number;
  ipWhitelist: string[];
  alertThresholds: {
    unknownFaces: number;
    failedLogins: number;
    suspiciousActivity: number;
  };
  encryptionKey: string;
  encryptionAlgorithm: 'AES-256' | 'AES-192' | 'AES-128';
}

const securitySchema = z.object({
  faceRecognitionEnabled: z.boolean(),
  faceRecognitionThreshold: z.number().min(0.1).max(1.0),
  motionDetectionEnabled: z.boolean(),
  motionSensitivity: z.number().min(1).max(10),
  twoFactorAuthRequired: z.boolean(),
  passwordPolicy: z.object({
    minLength: z.number().min(8).max(32),
    requireUppercase: z.boolean(),
    requireNumbers: z.boolean(),
    requireSpecialChars: z.boolean(),
    expiryDays: z.number().min(0).max(365),
  }),
  sessionTimeout: z.number().min(5).max(1440),
  ipWhitelist: z.array(z.string().ip()),
  alertThresholds: z.object({
    unknownFaces: z.number().min(1),
    failedLogins: z.number().min(1),
    suspiciousActivity: z.number().min(1),
  }),
  encryptionKey: z.string().min(32),
  encryptionAlgorithm: z.enum(['AES-256', 'AES-192', 'AES-128']),
});

export function SecuritySettings() {
  const [settings, setSettings] = useState<SecuritySettings>({
    faceRecognitionEnabled: true,
    faceRecognitionThreshold: 0.8,
    motionDetectionEnabled: true,
    motionSensitivity: 5,
    twoFactorAuthRequired: false,
    passwordPolicy: {
      minLength: 12,
      requireUppercase: true,
      requireNumbers: true,
      requireSpecialChars: true,
      expiryDays: 90,
    },
    sessionTimeout: 30,
    ipWhitelist: [],
    alertThresholds: {
      unknownFaces: 3,
      failedLogins: 5,
      suspiciousActivity: 10,
    },
    encryptionKey: '',
    encryptionAlgorithm: 'AES-256',
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});
  const [newIp, setNewIp] = useState('');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/security-settings');
      if (!response.ok) throw new Error('Failed to fetch security settings');
      const data = await response.json();
      setSettings(data);
    } catch (err) {
      setError('Failed to load security settings. Please try again.');
      console.error('Security settings fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const validateSettings = () => {
    try {
      securitySchema.parse(settings);
      setValidationErrors({});
      return true;
    } catch (err) {
      if (err instanceof z.ZodError) {
        const errors: {[key: string]: string} = {};
        err.errors.forEach((error) => {
          if (error.path) {
            errors[error.path.join('.')] = error.message;
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
      const response = await fetch('/api/admin/security-settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (!response.ok) throw new Error('Failed to save security settings');

      setSuccess('Security settings saved successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to save security settings. Please try again.');
      console.error('Security settings save error:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleAddIp = () => {
    if (newIp && !settings.ipWhitelist.includes(newIp)) {
      setSettings({
        ...settings,
        ipWhitelist: [...settings.ipWhitelist, newIp],
      });
      setNewIp('');
    }
  };

  const handleRemoveIp = (ip: string) => {
    setSettings({
      ...settings,
      ipWhitelist: settings.ipWhitelist.filter(item => item !== ip),
    });
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
          Security Settings
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
              Face Recognition Settings
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.faceRecognitionEnabled}
                  onChange={(e) => setSettings({ ...settings, faceRecognitionEnabled: e.target.checked })}
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  Enable Face Recognition
                  <Tooltip title="Enable face recognition for all compatible cameras">
                    <IconButton size="small" sx={{ ml: 1 }}>
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              }
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography gutterBottom>
              Recognition Threshold
              <Tooltip title="Minimum confidence level required for face recognition (0.1-1.0)">
                <IconButton size="small" sx={{ ml: 1 }}>
                  <InfoIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Typography>
            <Slider
              value={settings.faceRecognitionThreshold}
              onChange={(_, value) => setSettings({ ...settings, faceRecognitionThreshold: value as number })}
              min={0.1}
              max={1.0}
              step={0.1}
              marks
              valueLabelDisplay="auto"
              disabled={!settings.faceRecognitionEnabled}
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Motion Detection
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.motionDetectionEnabled}
                  onChange={(e) => setSettings({ ...settings, motionDetectionEnabled: e.target.checked })}
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  Enable Motion Detection
                  <Tooltip title="Enable motion detection for enhanced security">
                    <IconButton size="small" sx={{ ml: 1 }}>
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              }
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography gutterBottom>
              Motion Sensitivity
              <Tooltip title="Adjust motion detection sensitivity (1-10)">
                <IconButton size="small" sx={{ ml: 1 }}>
                  <InfoIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Typography>
            <Slider
              value={settings.motionSensitivity}
              onChange={(_, value) => setSettings({ ...settings, motionSensitivity: value as number })}
              min={1}
              max={10}
              marks
              valueLabelDisplay="auto"
              disabled={!settings.motionDetectionEnabled}
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Authentication Settings
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.twoFactorAuthRequired}
                  onChange={(e) => setSettings({ ...settings, twoFactorAuthRequired: e.target.checked })}
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  Require Two-Factor Authentication
                  <Tooltip title="Enforce 2FA for all users">
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
              label="Session Timeout (minutes)"
              value={settings.sessionTimeout}
              onChange={(e) => setSettings({ ...settings, sessionTimeout: Number(e.target.value) })}
              error={!!validationErrors.sessionTimeout}
              helperText={validationErrors.sessionTimeout}
              InputProps={{
                endAdornment: <InputAdornment position="end">minutes</InputAdornment>,
              }}
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Password Policy
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Minimum Password Length"
              value={settings.passwordPolicy.minLength}
              onChange={(e) => setSettings({
                ...settings,
                passwordPolicy: {
                  ...settings.passwordPolicy,
                  minLength: Number(e.target.value)
                }
              })}
              error={!!validationErrors['passwordPolicy.minLength']}
              helperText={validationErrors['passwordPolicy.minLength']}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Password Expiry"
              value={settings.passwordPolicy.expiryDays}
              onChange={(e) => setSettings({
                ...settings,
                passwordPolicy: {
                  ...settings.passwordPolicy,
                  expiryDays: Number(e.target.value)
                }
              })}
              error={!!validationErrors['passwordPolicy.expiryDays']}
              helperText={validationErrors['passwordPolicy.expiryDays']}
              InputProps={{
                endAdornment: <InputAdornment position="end">days</InputAdornment>,
              }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.passwordPolicy.requireUppercase}
                  onChange={(e) => setSettings({
                    ...settings,
                    passwordPolicy: {
                      ...settings.passwordPolicy,
                      requireUppercase: e.target.checked
                    }
                  })}
                />
              }
              label="Require Uppercase Letters"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.passwordPolicy.requireNumbers}
                  onChange={(e) => setSettings({
                    ...settings,
                    passwordPolicy: {
                      ...settings.passwordPolicy,
                      requireNumbers: e.target.checked
                    }
                  })}
                />
              }
              label="Require Numbers"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.passwordPolicy.requireSpecialChars}
                  onChange={(e) => setSettings({
                    ...settings,
                    passwordPolicy: {
                      ...settings.passwordPolicy,
                      requireSpecialChars: e.target.checked
                    }
                  })}
                />
              }
              label="Require Special Characters"
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Alert Thresholds
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              type="number"
              label="Unknown Faces Threshold"
              value={settings.alertThresholds.unknownFaces}
              onChange={(e) => setSettings({
                ...settings,
                alertThresholds: {
                  ...settings.alertThresholds,
                  unknownFaces: Number(e.target.value)
                }
              })}
              error={!!validationErrors['alertThresholds.unknownFaces']}
              helperText={validationErrors['alertThresholds.unknownFaces']}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              type="number"
              label="Failed Login Attempts"
              value={settings.alertThresholds.failedLogins}
              onChange={(e) => setSettings({
                ...settings,
                alertThresholds: {
                  ...settings.alertThresholds,
                  failedLogins: Number(e.target.value)
                }
              })}
              error={!!validationErrors['alertThresholds.failedLogins']}
              helperText={validationErrors['alertThresholds.failedLogins']}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              type="number"
              label="Suspicious Activity Threshold"
              value={settings.alertThresholds.suspiciousActivity}
              onChange={(e) => setSettings({
                ...settings,
                alertThresholds: {
                  ...settings.alertThresholds,
                  suspiciousActivity: Number(e.target.value)
                }
              })}
              error={!!validationErrors['alertThresholds.suspiciousActivity']}
              helperText={validationErrors['alertThresholds.suspiciousActivity']}
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Encryption Settings
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Encryption Algorithm</InputLabel>
              <Select
                value={settings.encryptionAlgorithm}
                label="Encryption Algorithm"
                onChange={(e) => setSettings({
                  ...settings,
                  encryptionAlgorithm: e.target.value as 'AES-256' | 'AES-192' | 'AES-128'
                })}
              >
                <MenuItem value="AES-256">AES-256</MenuItem>
                <MenuItem value="AES-192">AES-192</MenuItem>
                <MenuItem value="AES-128">AES-128</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="password"
              label="Encryption Key"
              value={settings.encryptionKey}
              onChange={(e) => setSettings({ ...settings, encryptionKey: e.target.value })}
              error={!!validationErrors.encryptionKey}
              helperText={validationErrors.encryptionKey}
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              IP Whitelist
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <TextField
                fullWidth
                label="IP Address"
                value={newIp}
                onChange={(e) => setNewIp(e.target.value)}
                placeholder="Enter IP address"
              />
              <Button
                variant="contained"
                onClick={handleAddIp}
                disabled={!newIp}
              >
                Add IP
              </Button>
            </Box>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {settings.ipWhitelist.map((ip) => (
                <Chip
                  key={ip}
                  label={ip}
                  onDelete={() => handleRemoveIp(ip)}
                  sx={{ mb: 1 }}
                />
              ))}
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
} 