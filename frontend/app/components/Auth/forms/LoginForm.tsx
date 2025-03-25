"use client"

import { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Divider
} from '@mui/material';
import { useAuth } from '@/hooks/useAuth';
import { RecognitionClient } from '@/components/features/recognition/RecognitionClient';
import { LoginCredentials } from '@/lib/auth/types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`auth-tabpanel-${index}`}
      aria-labelledby={`auth-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export function LoginForm() {
  const { login, loginWithFace } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [formData, setFormData] = useState<LoginCredentials>({
    email: '',
    password: ''
  });

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    setError(null);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleTraditionalLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await login(formData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleFaceLogin = async (faceData: string) => {
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('face', faceData);
      await loginWithFace(formData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Face login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleFaceCapture = async (formData: FormData) => {
    setLoading(true);
    setError(null);

    try {
      await loginWithFace(formData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Face login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleError = (err: Error) => {
    setError(err.message);
    setLoading(false);
  };

  return (
    <Card sx={{ maxWidth: 600, mx: 'auto', mt: 4 }}>
      <CardContent>
        <Typography variant="h5" component="h1" gutterBottom align="center">
          Login to CernoID
        </Typography>

        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="login methods"
            centered
          >
            <Tab label="Traditional Login" />
            <Tab label="Face Recognition" />
          </Tabs>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        <TabPanel value={tabValue} index={0}>
          <form onSubmit={handleTraditionalLogin}>
            <TextField
              fullWidth
              label="Email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleInputChange}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Password"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleInputChange}
              margin="normal"
              required
            />
            <Button
              type="submit"
              variant="contained"
              color="primary"
              fullWidth
              size="large"
              sx={{ mt: 3 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Login'}
            </Button>
          </form>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <RecognitionClient
            title="Face Login"
            description="Please look directly at the camera and ensure good lighting for face recognition."
            onCapture={handleFaceCapture}
            onError={handleError}
            showResults={false}
            recognitionOptions={{
              confidenceThreshold: 0.8,
              detectLandmarks: true,
              extractDescriptor: true
            }}
          />
        </TabPanel>

        <Divider sx={{ my: 2 }} />

        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Don't have an account?{' '}
            <Button
              href="/register"
              color="primary"
            >
              Register
            </Button>
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Forgot your password?{' '}
            <Button
              href="/forgot-password"
              color="primary"
            >
              Reset Password
            </Button>
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
} 