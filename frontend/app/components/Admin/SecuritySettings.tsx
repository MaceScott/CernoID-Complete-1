import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Switch,
  FormControlLabel,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Divider,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  Info as InfoIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

interface SecurityConfig {
  passwordPolicy: {
    minLength: number;
    requireUppercase: boolean;
    requireLowercase: boolean;
    requireNumbers: boolean;
    requireSpecialChars: boolean;
    maxAge: number;
    preventReuse: number;
  };
  sessionPolicy: {
    timeout: number;
    maxConcurrent: number;
    enforceIpLock: boolean;
  };
  faceRecognition: {
    minConfidence: number;
    maxAttempts: number;
    requireLiveness: boolean;
    antiSpoofing: boolean;
  };
  accessControl: {
    failedAttempts: number;
    lockoutDuration: number;
    requireMFA: boolean;
    allowedIPs: string[];
  };
}

export const SecuritySettings: React.FC = () => {
  const [config, setConfig] = useState<SecurityConfig>({
    passwordPolicy: {
      minLength: 8,
      requireUppercase: true,
      requireLowercase: true,
      requireNumbers: true,
      requireSpecialChars: true,
      maxAge: 90,
      preventReuse: 5,
    },
    sessionPolicy: {
      timeout: 30,
      maxConcurrent: 3,
      enforceIpLock: true,
    },
    faceRecognition: {
      minConfidence: 0.9,
      maxAttempts: 3,
      requireLiveness: true,
      antiSpoofing: true,
    },
    accessControl: {
      failedAttempts: 5,
      lockoutDuration: 15,
      requireMFA: true,
      allowedIPs: [],
    },
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchSecurityConfig();
  }, []);

  const fetchSecurityConfig = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/security/config`,
        {
          credentials: 'include',
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch security configuration');
      }

      const data = await response.json();
      setConfig(data);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch security configuration');
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/security/config`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify(config),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to update security configuration');
      }

      setSuccess('Security settings updated successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update security configuration');
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

      <Grid container spacing={3}>
        {/* Password Policy */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Password Policy
            </Typography>
            <Box sx={{ mt: 2 }}>
              <TextField
                fullWidth
                type="number"
                label="Minimum Length"
                value={config.passwordPolicy.minLength}
                onChange={(e) => setConfig({
                  ...config,
                  passwordPolicy: {
                    ...config.passwordPolicy,
                    minLength: parseInt(e.target.value),
                  },
                })}
                sx={{ mb: 2 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={config.passwordPolicy.requireUppercase}
                    onChange={(e) => setConfig({
                      ...config,
                      passwordPolicy: {
                        ...config.passwordPolicy,
                        requireUppercase: e.target.checked,
                      },
                    })}
                  />
                }
                label="Require Uppercase"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={config.passwordPolicy.requireLowercase}
                    onChange={(e) => setConfig({
                      ...config,
                      passwordPolicy: {
                        ...config.passwordPolicy,
                        requireLowercase: e.target.checked,
                      },
                    })}
                  />
                }
                label="Require Lowercase"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={config.passwordPolicy.requireNumbers}
                    onChange={(e) => setConfig({
                      ...config,
                      passwordPolicy: {
                        ...config.passwordPolicy,
                        requireNumbers: e.target.checked,
                      },
                    })}
                  />
                }
                label="Require Numbers"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={config.passwordPolicy.requireSpecialChars}
                    onChange={(e) => setConfig({
                      ...config,
                      passwordPolicy: {
                        ...config.passwordPolicy,
                        requireSpecialChars: e.target.checked,
                      },
                    })}
                  />
                }
                label="Require Special Characters"
              />
            </Box>
          </Paper>
        </Grid>

        {/* Face Recognition Settings */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Face Recognition
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography gutterBottom>
                Minimum Confidence Threshold
              </Typography>
              <Slider
                value={config.faceRecognition.minConfidence}
                onChange={(e, value) => setConfig({
                  ...config,
                  faceRecognition: {
                    ...config.faceRecognition,
                    minConfidence: value as number,
                  },
                })}
                min={0.5}
                max={1}
                step={0.05}
                valueLabelDisplay="auto"
                valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
                sx={{ mb: 2 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={config.faceRecognition.requireLiveness}
                    onChange={(e) => setConfig({
                      ...config,
                      faceRecognition: {
                        ...config.faceRecognition,
                        requireLiveness: e.target.checked,
                      },
                    })}
                  />
                }
                label="Require Liveness Detection"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={config.faceRecognition.antiSpoofing}
                    onChange={(e) => setConfig({
                      ...config,
                      faceRecognition: {
                        ...config.faceRecognition,
                        antiSpoofing: e.target.checked,
                      },
                    })}
                  />
                }
                label="Enable Anti-spoofing"
              />
            </Box>
          </Paper>
        </Grid>

        {/* Access Control */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Access Control
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Max Failed Attempts"
                  value={config.accessControl.failedAttempts}
                  onChange={(e) => setConfig({
                    ...config,
                    accessControl: {
                      ...config.accessControl,
                      failedAttempts: parseInt(e.target.value),
                    },
                  })}
                  sx={{ mb: 2 }}
                />
                <TextField
                  fullWidth
                  type="number"
                  label="Lockout Duration (minutes)"
                  value={config.accessControl.lockoutDuration}
                  onChange={(e) => setConfig({
                    ...config,
                    accessControl: {
                      ...config.accessControl,
                      lockoutDuration: parseInt(e.target.value),
                    },
                  })}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.accessControl.requireMFA}
                      onChange={(e) => setConfig({
                        ...config,
                        accessControl: {
                          ...config.accessControl,
                          requireMFA: e.target.checked,
                        },
                      })}
                    />
                  }
                  label="Require Multi-Factor Authentication"
                />
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchSecurityConfig}
          disabled={saving}
        >
          Reset
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
  );
}; 