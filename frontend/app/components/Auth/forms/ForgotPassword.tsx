'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Box,
  Button,
  TextField,
  Typography,
  CircularProgress,
  Link as MuiLink,
  InputAdornment,
  Alert,
  LinearProgress,
} from '@mui/material';
import {
  Email as EmailIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { z } from 'zod';

const MotionBox = motion(Box);

const emailSchema = z.string().email('Please enter a valid email address');

interface ValidationError {
  email?: string;
}

export function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<ValidationError>({});
  const [success, setSuccess] = useState(false);
  const router = useRouter();

  const validateEmail = (): boolean => {
    try {
      emailSchema.parse(email);
      setValidationError({});
      return true;
    } catch (err) {
      if (err instanceof z.ZodError) {
        setValidationError({ email: err.errors[0].message });
      }
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateEmail()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to send reset email');
      }

      setSuccess(true);
    } catch (err) {
      console.error('Password reset error:', err);
      setError(err instanceof Error ? err.message : 'Failed to send reset email. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (success) {
    return (
      <MotionBox
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        sx={{ textAlign: 'center', width: '100%' }}
      >
        <Typography variant="h5" sx={{ mb: 2, fontWeight: 600 }}>
          Check Your Email
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          If an account exists with the email you provided, you will receive password reset instructions.
        </Typography>
        <MuiLink
          component={Link}
          href="/login"
          underline="none"
        >
          <Button
            variant="contained"
            startIcon={<ArrowBackIcon />}
            sx={{ minWidth: 200 }}
          >
            Return to Login
          </Button>
        </MuiLink>
      </MotionBox>
    );
  }

  return (
    <MotionBox
      component="form"
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      sx={{ width: '100%' }}
    >
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          </motion.div>
        )}
      </AnimatePresence>

      <TextField
        fullWidth
        margin="normal"
        label="Email"
        type="email"
        value={email}
        onChange={(e) => {
          setEmail(e.target.value);
          setError(null);
          setValidationError({});
        }}
        error={!!validationError.email}
        helperText={validationError.email}
        disabled={isSubmitting}
        required
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <EmailIcon color="action" />
            </InputAdornment>
          ),
        }}
        sx={{ mb: 3 }}
      />

      <Button
        type="submit"
        fullWidth
        variant="contained"
        disabled={isSubmitting}
        sx={{ 
          mb: 2,
          py: 1.5,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {isSubmitting ? (
          <CircularProgress size={24} sx={{ color: 'white' }} />
        ) : (
          'Send Reset Instructions'
        )}
        {isSubmitting && (
          <LinearProgress
            sx={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: 2,
            }}
          />
        )}
      </Button>

      <MuiLink
        component={Link}
        href="/login"
        underline="none"
      >
        <Button
          fullWidth
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          sx={{ py: 1.5 }}
        >
          Back to Login
        </Button>
      </MuiLink>
    </MotionBox>
  );
} 