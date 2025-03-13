'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
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
  const { login, loginWithFace } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const router = useRouter();
  const mounted = useRef(false);
  const [showCameraDialog, setShowCameraDialog] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [credentials, setCredentials] = useState<LoginCredentials>({
    email: '',
    password: '',
  });

  // Reset form state on mount
  useEffect(() => {
    mounted.current = true;
    // Reset all form state
    setCredentials({ email: '', password: '' });
    setError(null);
    setValidationErrors({});
    setShowPassword(false);
    return () => {
      mounted.current = false;
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
    setError(null);
    
    if (validationErrors[name as keyof ValidationErrors]) {
      setValidationErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await login(credentials);
      
      if (response.success) {
        // Clear form state
        setCredentials({ email: '', password: '' });
        setValidationErrors({});
        setShowPassword(false);
        
        // Use Next.js router for navigation
        router.replace('/dashboard');
      } else {
        throw new Error(response.error || 'Invalid email or password');
      }
    } catch (err) {
      console.error('Login error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Invalid email or password';
      setError(errorMessage);
      // Only clear password on error, keep email
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

      const video = document.createElement('video');
      video.srcObject = stream;
      video.setAttribute('playsinline', 'true');
      video.setAttribute('autoplay', 'true');
      await video.play();

      // Wait for video to be ready
      await new Promise((resolve) => {
        video.onloadedmetadata = () => {
          video.play();
          resolve(true);
        };
      });

      // Give more time for face detection
      await new Promise(resolve => setTimeout(resolve, 3000));

      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const context = canvas.getContext('2d');
      if (!context) throw new Error('Could not get canvas context');

      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      stream.getTracks().forEach(track => track.stop());

      const imageData = canvas.toDataURL('image/jpeg', 0.8);
      
      const response = await loginWithFace(imageData);
      
      if (response.success) {
        // Use Next.js router for navigation
        router.replace('/dashboard');
      } else {
        throw new Error(response.error || 'Face not recognized. Please try again.');
      }
    } catch (err) {
      console.error('Face login error:', err);
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
      <form onSubmit={handleSubmit} noValidate>
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
                <Tooltip title={showPassword ? "Hide password" : "Show password"}>
                  <IconButton
                    aria-label="toggle password visibility"
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </Tooltip>
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />

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
            'Sign In'
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

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <MuiLink
            component={Link}
            href="/forgot-password"
            variant="body2"
            underline="hover"
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              color: 'text.secondary',
              '&:hover': {
                color: 'primary.main',
              },
            }}
          >
            <InfoIcon sx={{ fontSize: 16 }} />
            Forgot password?
          </MuiLink>
          <MuiLink
            component={Link}
            href="/register"
            variant="body2"
            underline="hover"
            sx={{
              color: 'text.secondary',
              '&:hover': {
                color: 'primary.main',
              },
            }}
          >
            Create an account
          </MuiLink>
        </Box>

        <Divider sx={{ my: 2 }}>
          <Typography variant="body2" color="text.secondary">
            OR
          </Typography>
        </Divider>

        <Button
          fullWidth
          variant="outlined"
          onClick={handleFaceLogin}
          disabled={isSubmitting}
          startIcon={<FaceIcon />}
          sx={{ 
            py: 1.5,
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          Sign in with Face ID
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
      </form>

      <Dialog
        open={showCameraDialog}
        onClose={() => {
          if (!isSubmitting) {
            setShowCameraDialog(false);
          }
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <VideocamIcon />
            <Typography>Face Recognition</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {cameraError ? (
            <Alert severity="error" sx={{ mt: 2 }}>
              {cameraError}
            </Alert>
          ) : (
            <Box sx={{ textAlign: 'center', py: 2 }}>
              <CircularProgress />
              <Typography sx={{ mt: 2 }}>
                Please look at the camera for face recognition...
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setShowCameraDialog(false)}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
        </DialogActions>
      </Dialog>
    </MotionBox>
  );
}; 