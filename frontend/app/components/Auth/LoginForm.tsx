'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useContext } from 'react';
import { AuthContext } from '@/providers/AuthProvider';
import { LoginCredentials } from '@/lib/auth/types';
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
  IconButton,
  Alert,
  Divider,
  LinearProgress,
  Tooltip,
  Collapse,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Face as FaceIcon,
  Email as EmailIcon,
  Lock as LockIcon,
  Info as InfoIcon,
  Videocam as VideocamIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

const MotionBox = motion(Box);

interface ValidationErrors {
  email?: string;
  password?: string;
}

export const LoginForm = () => {
  const { login, loginWithFace } = useContext(AuthContext);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const router = useRouter();
  const mounted = useRef(false);
  const [showCameraDialog, setShowCameraDialog] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [credentials, setCredentials] = useState<LoginCredentials>(() => {
    // Try to get stored email from localStorage
    const storedEmail = typeof window !== 'undefined' ? localStorage.getItem('lastEmail') : null;
    return {
      email: storedEmail || '',
      password: '',
    };
  });
  const formRef = useRef<HTMLFormElement>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      // Cleanup camera stream if component unmounts
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const validateForm = (): boolean => {
    const errors: ValidationErrors = {};
    
    if (!credentials.email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(credentials.email)) {
      errors.email = 'Please enter a valid email address';
    }

    if (!credentials.password) {
      errors.password = 'Password is required';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({ ...prev, [name]: value }));
    
    // Store email in localStorage when it changes
    if (name === 'email' && typeof window !== 'undefined') {
      localStorage.setItem('lastEmail', value);
    }
    
    // Clear error when user starts typing
    setError(null);
    
    // Clear validation error for the field being edited
    if (validationErrors[name as keyof ValidationErrors]) {
      setValidationErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setValidationErrors({});

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await login(credentials);
      
      if (!response.success) {
        setError(response.error || 'Invalid email or password');
        setCredentials(prev => ({ ...prev, password: '' }));
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Invalid email or password';
      setError(errorMessage);
      setCredentials(prev => ({ ...prev, password: '' }));
    } finally {
      if (mounted.current) {
        setIsSubmitting(false);
      }
    }
  };

  const handleFaceLogin = async () => {
    setError(null);
    setCameraError(null);
    setIsSubmitting(true);
    setShowCameraDialog(true);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user'
        }
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();

        // Wait for video to stabilize
        await new Promise(resolve => setTimeout(resolve, 2000));

        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        const context = canvas.getContext('2d');
        if (!context) throw new Error('Could not get canvas context');

        context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        
        const response = await loginWithFace(imageData);
        
        if (!response.success) {
          throw new Error(response.error || 'Face not recognized. Please try again.');
        }
      }
    } catch (err) {
      if (err instanceof Error) {
        if (err.name === 'NotAllowedError') {
          setCameraError('Camera access was denied. Please allow camera access and try again.');
        } else if (err.name === 'NotFoundError') {
          setCameraError('No camera found. Please connect a camera and try again.');
        } else {
          setCameraError(err.message);
        }
      } else {
        setCameraError('Face recognition failed. Please try again or use email/password.');
      }
    } finally {
      if (mounted.current) {
        setIsSubmitting(false);
        setShowCameraDialog(false);
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
      }
    }
  };

  return (
    <MotionBox
      component="div"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.2 }}
      sx={{ width: '100%' }}
    >
      <form ref={formRef} onSubmit={handleSubmit} noValidate>
        <TextField
          fullWidth
          margin="normal"
          label="Email"
          name="email"
          type="email"
          autoComplete="email"
          value={credentials.email}
          onChange={handleInputChange}
          error={!!validationErrors.email}
          helperText={validationErrors.email}
          required
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <EmailIcon color="action" />
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />

        <TextField
          fullWidth
          margin="normal"
          label="Password"
          name="password"
          type={showPassword ? 'text' : 'password'}
          autoComplete="current-password"
          value={credentials.password}
          onChange={handleInputChange}
          error={!!validationErrors.password}
          helperText={validationErrors.password}
          required
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <LockIcon color="action" />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  aria-label="toggle password visibility"
                  onClick={() => setShowPassword(!showPassword)}
                  edge="end"
                >
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Button
          fullWidth
          variant="contained"
          color="primary"
          type="submit"
          disabled={isSubmitting}
          sx={{ mb: 2 }}
        >
          {isSubmitting ? <CircularProgress size={24} /> : 'Sign In'}
        </Button>

        <Divider sx={{ my: 2 }}>OR</Divider>

        <Button
          fullWidth
          variant="outlined"
          color="primary"
          onClick={handleFaceLogin}
          disabled={isSubmitting}
          startIcon={<FaceIcon />}
          sx={{ mb: 2 }}
        >
          Sign In with Face ID
        </Button>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
          <Link href="/forgot-password" passHref>
            <MuiLink variant="body2">
              Forgot password?
            </MuiLink>
          </Link>
          <Link href="/register" passHref>
            <MuiLink variant="body2">
              Don't have an account? Sign Up
            </MuiLink>
          </Link>
        </Box>
      </form>

      <Dialog
        open={showCameraDialog}
        onClose={() => {
          setShowCameraDialog(false);
          if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
          }
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Face ID Login</DialogTitle>
        <DialogContent>
          {cameraError ? (
            <Alert severity="error" sx={{ mt: 2 }}>
              {cameraError}
            </Alert>
          ) : (
            <>
              <Typography variant="body1" sx={{ mb: 2 }}>
                Please look directly at the camera and ensure good lighting.
              </Typography>
              <Box
                sx={{
                  position: 'relative',
                  width: '100%',
                  height: 480,
                  backgroundColor: 'black',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                }}
              >
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                  }}
                />
                {isSubmitting && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'center',
                      alignItems: 'center',
                      backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    }}
                  >
                    <CircularProgress color="primary" size={64} />
                    <Typography variant="h6" color="white" sx={{ mt: 2 }}>
                      Verifying...
                    </Typography>
                  </Box>
                )}
              </Box>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setShowCameraDialog(false);
              if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
                streamRef.current = null;
              }
            }}
          >
            Cancel
          </Button>
          {cameraError && (
            <Button
              onClick={() => {
                setCameraError(null);
                handleFaceLogin();
              }}
              variant="contained"
            >
              Try Again
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </MotionBox>
  );
}; 