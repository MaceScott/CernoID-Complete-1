/**
 * File: LoginForm.tsx
 * Purpose: Provides the main login interface component with both traditional and face recognition authentication.
 * 
 * Key Features:
 * - Email/password authentication
 * - Face recognition login
 * - Form validation
 * - Real-time face detection using face-api.js
 * - Responsive UI with Material-UI components
 * - Animated transitions using Framer Motion
 * 
 * Dependencies:
 * - face-api.js: Face detection and recognition
 * - @mui/material: UI components
 * - framer-motion: Animation library
 * - next/navigation: Routing
 * - AuthContext: Authentication state management
 * 
 * Expected Inputs:
 * - User email and password for traditional login
 * - Camera access for face recognition
 * 
 * Expected Outputs:
 * - Authentication success/failure
 * - Redirection to dashboard on success
 * - Error messages on failure
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useContext } from 'react';
import { AuthContext } from '@/providers/AuthProvider';
import { LoginCredentials } from '@/lib/auth/types';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Script from 'next/script';
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

declare global {
  interface Window {
    faceapi: any;
  }
}

const MotionBox = motion(Box);

/**
 * Interface for form validation errors
 */
interface ValidationErrors {
  email?: string;
  password?: string;
}

/**
 * LoginForm Component
 * 
 * A comprehensive login form component that provides both traditional
 * email/password authentication and face recognition capabilities.
 * Includes form validation, error handling, and loading states.
 */
export const LoginForm = () => {
  const { login, loginWithFace, isLoading, error, clearError } = useContext(AuthContext);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [showPassword, setShowPassword] = useState(false);
  const [credentials, setCredentials] = useState<LoginCredentials>({
    email: '',
    password: '',
  });
  const formRef = useRef<HTMLFormElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const mounted = useRef(true);
  const router = useRouter();
  const [showCameraDialog, setShowCameraDialog] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [modelsLoaded, setModelsLoaded] = useState(false);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loginAttempts, setLoginAttempts] = useState(0);
  const [lockoutUntil, setLockoutUntil] = useState<Date | null>(null);
  const MAX_LOGIN_ATTEMPTS = 5;
  const LOCKOUT_DURATION = 15 * 60 * 1000; // 15 minutes

  // Clear form on mount
  useEffect(() => {
    if (formRef.current) {
      formRef.current.reset();
    }
    setCredentials({ email: '', password: '' });
    clearError();
  }, []);

  // Clear form and errors on unmount
  useEffect(() => {
    return () => {
      if (formRef.current) {
        formRef.current.reset();
      }
      setCredentials({ email: '', password: '' });
      clearError();
    };
  }, [clearError]);

  // Clear password on error
  useEffect(() => {
    if (error) {
      setCredentials(prev => ({ ...prev, password: '' }));
    }
  }, [error]);

  useEffect(() => {
    const loadModels = async () => {
      if (!window.faceapi) {
        console.error('Face-api.js not loaded');
        return;
      }

      setIsLoadingModels(true);
      try {
        const modelPath = '/models';
        
        // Check if models are already loaded
        if (window.faceapi.nets.tinyFaceDetector.isLoaded &&
            window.faceapi.nets.faceLandmark68Net.isLoaded &&
            window.faceapi.nets.faceRecognitionNet.isLoaded) {
          console.log('Models already loaded');
          setModelsLoaded(true);
          return;
        }

        console.log('Loading face detection models...');
        
        // Load models with progress tracking
        const loadModel = async (model: any, name: string) => {
          try {
            await model.loadFromUri(`${modelPath}`);
            console.log(`Loaded ${name} model`);
          } catch (error) {
            console.error(`Error loading ${name} model:`, error);
            throw error;
          }
        };

        await Promise.all([
          loadModel(window.faceapi.nets.tinyFaceDetector, 'face detector'),
          loadModel(window.faceapi.nets.faceLandmark68Net, 'landmarks'),
          loadModel(window.faceapi.nets.faceRecognitionNet, 'recognition'),
        ]);

        console.log('All models loaded successfully');
        setModelsLoaded(true);
      } catch (err) {
        console.error('Error loading face detection models:', err);
        setCameraError('Failed to load face detection models. Please try again later.');
        setModelsLoaded(false);
      } finally {
        setIsLoadingModels(false);
      }
    };

    // Load models when face-api.js is available
    if (window.faceapi) {
      loadModels();
    }
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
    clearError();
    
    // Clear validation error for the field being edited
    if (validationErrors[name as keyof ValidationErrors]) {
      setValidationErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const validatePassword = (password: string): { isValid: boolean; errors: string[] } => {
    const errors: string[] = [];
    
    if (password.length < 8) {
      errors.push('Password must be at least 8 characters long');
    }
    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }
    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter');
    }
    if (!/[0-9]/.test(password)) {
      errors.push('Password must contain at least one number');
    }
    if (!/[!@#$%^&*]/.test(password)) {
      errors.push('Password must contain at least one special character (!@#$%^&*)');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('[LoginForm] Form submission started');
    
    // Check for lockout
    if (lockoutUntil && new Date() < lockoutUntil) {
      const remainingTime = Math.ceil((lockoutUntil.getTime() - new Date().getTime()) / 1000 / 60);
      setError(`Too many login attempts. Please try again in ${remainingTime} minutes.`);
      return;
    }

    if (!validateForm() || isLoading) {
      console.log('[LoginForm] Validation failed or form is loading');
      return;
    }

    // Validate password strength for new registrations
    if (isRegistering) {
      const { isValid, errors } = validatePassword(credentials.password);
      if (!isValid) {
        setError(errors.join('\n'));
        return;
      }
    }

    try {
      console.log('[LoginForm] Calling login with credentials:', { email: credentials.email });
      const result = await login(credentials);
      console.log('[LoginForm] Login result:', result);
      
      if (!result.success) {
        // Increment login attempts
        const newAttempts = loginAttempts + 1;
        setLoginAttempts(newAttempts);

        // Check if should lockout
        if (newAttempts >= MAX_LOGIN_ATTEMPTS) {
          const lockoutTime = new Date(new Date().getTime() + LOCKOUT_DURATION);
          setLockoutUntil(lockoutTime);
          setError(`Too many failed login attempts. Account locked for ${LOCKOUT_DURATION / 1000 / 60} minutes.`);
        }

        // Clear password on failed attempt
        setCredentials(prev => ({ ...prev, password: '' }));
      } else {
        // Reset attempts on successful login
        setLoginAttempts(0);
        setLockoutUntil(null);
      }
    } catch (err) {
      console.error('[LoginForm] Login error:', err);
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    }
  };

  const handleLoginSuccess = async () => {
    if (mounted.current) {
      setShowCameraDialog(false);
      setIsSubmitting(false);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
    }
  };

  /**
   * Handles face recognition login process
   * - Initializes camera
   * - Sets up face detection
   * - Processes face data for authentication
   */
  const handleFaceLogin = async () => {
    if (!window.faceapi) {
      setCameraError('Face detection is not available. Please try again later.');
      return;
    }

    if (!modelsLoaded) {
      setCameraError('Face detection models are not loaded yet. Please wait.');
      return;
    }

    clearError();
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
      
      if (!videoRef.current || !canvasRef.current) {
        throw new Error('Video or canvas elements not initialized');
      }

      streamRef.current = stream;
      videoRef.current.srcObject = stream;

      await new Promise<void>((resolve) => {
        if (videoRef.current) {
          videoRef.current.onloadedmetadata = () => resolve();
        }
      });

      await videoRef.current.play();

      // Set up canvas dimensions
      canvasRef.current.width = videoRef.current.videoWidth;
      canvasRef.current.height = videoRef.current.videoHeight;

      // Start face detection loop
      const detectFace = async () => {
        if (!videoRef.current || !canvasRef.current || !streamRef.current) {
          throw new Error('Video or canvas elements not available');
        }

        try {
          const detections = await window.faceapi.detectSingleFace(
            videoRef.current,
            new window.faceapi.TinyFaceDetectorOptions()
          );

          if (detections) {
            // Draw detections
            const ctx = canvasRef.current.getContext('2d');
            if (ctx) {
              ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
              window.faceapi.draw.drawDetections(canvasRef.current, [detections]);
            }

            // Capture the face image
            const canvas = document.createElement('canvas');
            canvas.width = videoRef.current.videoWidth;
            canvas.height = videoRef.current.videoHeight;
            const ctx2 = canvas.getContext('2d');
            if (!ctx2) {
              throw new Error('Failed to get canvas context');
            }
            ctx2.drawImage(videoRef.current, 0, 0);
            const imageData = canvas.toDataURL('image/jpeg');

            // Stop the camera
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;

            // Attempt face login
            const response = await loginWithFace(imageData);
            if (!response.success) {
              throw new Error(response.error || 'Face login failed');
            }

            await handleLoginSuccess();
          } else {
            // Continue detection if no face is found
            requestAnimationFrame(detectFace);
          }
        } catch (error) {
          console.error('Face detection error:', error);
          throw error;
        }
      };

      detectFace();
    } catch (error) {
      console.error('Face login error:', error);
      setCameraError(error instanceof Error ? error.message : 'Failed to initialize camera');
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
    } finally {
      if (mounted.current) {
        setIsSubmitting(false);
        setShowCameraDialog(false);
      }
    }
  };

  /**
   * Camera Dialog Component
   * Displays the camera feed for face recognition
   * Includes error handling and user instructions
   */
  const CameraDialog = () => (
    <Dialog open={showCameraDialog} onClose={() => setShowCameraDialog(false)}>
      <DialogTitle>Face Login</DialogTitle>
      <DialogContent>
        {cameraError ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {cameraError}
          </Alert>
        ) : (
          <>
            <Box sx={{ position: 'relative', width: '100%', height: 'auto' }}>
              <video
                ref={videoRef}
                style={{
                  width: '100%',
                  height: 'auto',
                  transform: 'scaleX(-1)',
                }}
                autoPlay
                playsInline
                muted
              />
              <canvas
                ref={canvasRef}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  transform: 'scaleX(-1)',
                }}
              />
            </Box>
            <Typography variant="body2" color="textSecondary" sx={{ mt: 2, textAlign: 'center' }}>
              Position your face in the camera view
            </Typography>
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => {
          if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
          }
          setShowCameraDialog(false);
        }}>
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <>
      <Script
        src="https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js"
        strategy="afterInteractive"
        onLoad={() => {
          console.log('Face-api.js script loaded');
          if (window.faceapi) {
            console.log('Face-api.js loaded successfully');
            setModelsLoaded(false);
            setIsLoadingModels(true);
          } else {
            console.error('Face-api.js failed to load');
            setCameraError('Failed to load face detection library');
            setIsLoadingModels(false);
          }
        }}
        onError={(e) => {
          console.error('Error loading face-api.js:', e);
          setCameraError('Failed to load face detection library');
          setModelsLoaded(false);
          setIsLoadingModels(false);
        }}
      />
      <MotionBox
        component="div"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        sx={{ width: '100%' }}
      >
        <form ref={formRef} onSubmit={handleSubmit} noValidate>
          <Box sx={{ mb: 3 }}>
            <TextField
              fullWidth
              label="Email"
              name="email"
              type="email"
              value={credentials.email}
              onChange={handleInputChange}
              error={!!validationErrors.email || !!error}
              helperText={validationErrors.email}
              disabled={isLoading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <EmailIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Box>

          <Box sx={{ mb: 3 }}>
            <TextField
              fullWidth
              label="Password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              value={credentials.password}
              onChange={handleInputChange}
              error={!!validationErrors.password || !!error}
              helperText={validationErrors.password}
              disabled={isLoading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LockIcon />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                      disabled={isLoading}
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 2 }}>
            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={isLoading}
              startIcon={isLoading ? <CircularProgress size={20} /> : null}
            >
              Sign In
            </Button>

            <Button
              type="button"
              variant="outlined"
              fullWidth
              onClick={handleFaceLogin}
              disabled={isLoading || isLoadingModels}
              startIcon={
                isLoadingModels ? (
                  <CircularProgress size={20} />
                ) : (
                  <FaceIcon />
                )
              }
            >
              Sign In with Face ID
            </Button>
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Button
              component={Link}
              href="/forgot-password"
              variant="text"
              disabled={isLoading}
            >
              Forgot Password?
            </Button>
            <Button
              component={Link}
              href="/register"
              variant="text"
              disabled={isLoading}
            >
              Create Account
            </Button>
          </Box>
        </form>
      </MotionBox>

      <CameraDialog />
    </>
  );
}; 