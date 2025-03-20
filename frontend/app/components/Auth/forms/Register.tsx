'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { RegisterData } from '@/lib/auth/types';
import { useRouter } from 'next/navigation';
import {
  Box,
  Button,
  Paper,
  TextField,
  Typography,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  LinearProgress,
  Alert,
  useTheme,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';
import zxcvbn from 'zxcvbn';

const MotionPaper = motion(Paper);
const MotionBox = motion(Box);

interface PasswordStrength {
  score: number;
  feedback: {
    warning: string;
    suggestions: string[];
  };
}

export const Register = () => {
  const { register } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [passwordStrength, setPasswordStrength] = useState<PasswordStrength | null>(null);
  const [registrationComplete, setRegistrationComplete] = useState(false);
  const router = useRouter();
  const theme = useTheme();

  const [credentials, setCredentials] = useState<RegisterData>({
    email: '',
    password: '',
    name: '',
    confirmPassword: '',
  });

  const steps = ['Personal Info', 'Security', 'Confirmation'];

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials((prev: RegisterData) => ({ ...prev, [name]: value }));

    if (name === 'password') {
      const result = zxcvbn(value);
      setPasswordStrength({
        score: result.score,
        feedback: result.feedback,
      });
    }
  };

  const validateStep = () => {
    switch (activeStep) {
      case 0:
        return credentials.name.length >= 2 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(credentials.email);
      case 1:
        return credentials.password.length >= 8 && 
               credentials.password === credentials.confirmPassword &&
               (passwordStrength?.score ?? 0) >= 2;
      default:
        return true;
    }
  };

  const handleNext = () => {
    if (validateStep()) {
      setActiveStep((prev: number) => prev + 1);
      setError(null);
    }
  };

  const handleBack = () => {
    setActiveStep((prev: number) => prev - 1);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateStep()) return;

    setError(null);
    setIsSubmitting(true);

    try {
      const response = await register(credentials);
      if (response.success) {
        setRegistrationComplete(true);
        setTimeout(() => {
          router.push('/dashboard');
        }, 3000);
      } else {
        throw new Error(response.error || 'Registration failed');
      }
    } catch (err) {
      console.error('Registration error:', err);
      setError(err instanceof Error ? err.message : 'Registration failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getPasswordStrengthColor = () => {
    if (!passwordStrength) return theme.palette.grey[300];
    const colors = ['#ff4444', '#ffbb33', '#00C851', '#007E33', '#00695C'];
    return colors[passwordStrength.score];
  };

  if (registrationComplete) {
    return (
      <MotionBox
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          p: 4,
        }}
      >
        <Typography variant="h4" gutterBottom sx={{ color: theme.palette.success.main }}>
          Registration Successful!
        </Typography>
        <Typography variant="body1" sx={{ mb: 3 }}>
          Welcome to CernoID Security. Redirecting you to the dashboard...
        </Typography>
        <CircularProgress />
      </MotionBox>
    );
  }

  return (
    <Box sx={{ 
      width: '100%', 
      maxWidth: 600,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
    }}>
      <MotionBox
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        sx={{ mb: 4, textAlign: 'center' }}
      >
        <Typography
          variant="h3"
          component="h1"
          sx={{
            fontWeight: 600,
            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 1,
          }}
        >
          CernoID Security
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Create your account to get started
        </Typography>
      </MotionBox>

      <Stepper activeStep={activeStep} sx={{ width: '100%', mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <MotionPaper
        elevation={3}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        sx={{
          p: 4,
          width: '100%',
          borderRadius: 2,
          bgcolor: 'background.paper',
        }}
      >
        <form onSubmit={handleSubmit}>
          <AnimatePresence mode="wait">
            {activeStep === 0 && (
              <MotionBox
                key="step1"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
              >
                <TextField
                  fullWidth
                  margin="normal"
                  label="Name"
                  name="name"
                  type="text"
                  value={credentials.name}
                  onChange={handleInputChange}
                  required
                  autoComplete="name"
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  margin="normal"
                  label="Email"
                  name="email"
                  type="email"
                  value={credentials.email}
                  onChange={handleInputChange}
                  required
                  autoComplete="email"
                  sx={{ mb: 2 }}
                />
              </MotionBox>
            )}

            {activeStep === 1 && (
              <MotionBox
                key="step2"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
              >
                <TextField
                  fullWidth
                  margin="normal"
                  label="Password"
                  name="password"
                  type="password"
                  value={credentials.password}
                  onChange={handleInputChange}
                  required
                  autoComplete="new-password"
                  sx={{ mb: 1 }}
                />

                <Box sx={{ mb: 2 }}>
                  <LinearProgress
                    variant="determinate"
                    value={(passwordStrength?.score || 0) * 25}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      bgcolor: theme.palette.grey[200],
                      '& .MuiLinearProgress-bar': {
                        bgcolor: getPasswordStrengthColor(),
                      },
                    }}
                  />
                  {passwordStrength && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                      {passwordStrength.feedback.warning || 
                       (passwordStrength.score >= 3 ? 'Strong password!' : 'Consider a stronger password')}
                    </Typography>
                  )}
                </Box>

                <TextField
                  fullWidth
                  margin="normal"
                  label="Confirm Password"
                  name="confirmPassword"
                  type="password"
                  value={credentials.confirmPassword}
                  onChange={handleInputChange}
                  required
                  autoComplete="new-password"
                  error={credentials.password !== credentials.confirmPassword && credentials.confirmPassword !== ''}
                  helperText={
                    credentials.password !== credentials.confirmPassword && credentials.confirmPassword !== ''
                      ? 'Passwords do not match'
                      : ''
                  }
                  sx={{ mb: 2 }}
                />
              </MotionBox>
            )}

            {activeStep === 2 && (
              <MotionBox
                key="step3"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
              >
                <Alert severity="info" sx={{ mb: 3 }}>
                  Please review your information before completing registration
                </Alert>
                <Typography variant="body1" gutterBottom>
                  <strong>Name:</strong> {credentials.name}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Email:</strong> {credentials.email}
                </Typography>
              </MotionBox>
            )}
          </AnimatePresence>

          {error && (
            <Typography color="error" variant="body2" sx={{ mb: 2, textAlign: 'center' }}>
              {error}
            </Typography>
          )}

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
            <Button
              onClick={handleBack}
              disabled={activeStep === 0 || isSubmitting}
            >
              Back
            </Button>
            {activeStep === steps.length - 1 ? (
              <Button
                variant="contained"
                type="submit"
                disabled={isSubmitting || !validateStep()}
              >
                {isSubmitting ? <CircularProgress size={24} /> : 'Complete Registration'}
              </Button>
            ) : (
              <Button
                variant="contained"
                onClick={handleNext}
                disabled={!validateStep()}
              >
                Next
              </Button>
            )}
          </Box>
        </form>
      </MotionPaper>
    </Box>
  );
}; 