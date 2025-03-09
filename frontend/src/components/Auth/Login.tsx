'use client';

import React from 'react';
import { useState, useRef } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Button, TextField, Box, Typography, Container, Alert, Link } from '@mui/material';
import type { LoginCredentials } from '@/lib/auth/types';

export const Login = () => {
  const { login, loginWithFace, error } = useAuth();
  const [credentials, setCredentials] = useState<LoginCredentials>({
    email: '',
    password: '',
    remember: true,
  });
  const [useFaceRecognition, setUseFaceRecognition] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(credentials);
    } catch (err) {
      console.error('Login failed:', err);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value,
    });
  };

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setStream(mediaStream);
      setUseFaceRecognition(true);
    } catch (err) {
      console.error('Failed to access camera:', err);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setUseFaceRecognition(false);
  };

  const captureAndLogin = async () => {
    if (!videoRef.current) return;

    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext('2d');
    
    if (ctx && videoRef.current) {
      ctx.drawImage(videoRef.current, 0, 0);
      const imageData = canvas.toDataURL('image/jpeg');
      
      try {
        await loginWithFace(imageData);
        stopCamera();
      } catch (err) {
        console.error('Face recognition login failed:', err);
      }
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Typography component="h1" variant="h5">
          Sign in to CernoID
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mt: 2, width: '100%' }}>
            {error}
          </Alert>
        )}

        {useFaceRecognition ? (
          <Box sx={{ mt: 2, width: '100%', textAlign: 'center' }}>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              style={{ width: '100%', maxWidth: '400px', borderRadius: '8px' }}
            />
            <Box sx={{ mt: 2 }}>
              <Button
                onClick={captureAndLogin}
                variant="contained"
                color="primary"
                sx={{ mr: 1 }}
              >
                Verify Face
              </Button>
              <Button
                onClick={stopCamera}
                variant="outlined"
                color="secondary"
              >
                Cancel
              </Button>
            </Box>
          </Box>
        ) : (
          <Box component="form" onSubmit={handleLogin} sx={{ mt: 1, width: '100%' }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Username"
              name="username"
              autoComplete="username"
              autoFocus
              value={credentials.email}
              onChange={handleChange}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type="password"
              id="password"
              autoComplete="current-password"
              value={credentials.password}
              onChange={handleChange}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
            >
              Sign In
            </Button>
            <Button
              fullWidth
              variant="outlined"
              onClick={startCamera}
              sx={{ mb: 2 }}
            >
              Sign In with Face Recognition
            </Button>
            <Box sx={{ textAlign: 'center' }}>
              <Link href="/register" variant="body2">
                Don't have an account? Sign up
              </Link>
            </Box>
          </Box>
        )}
      </Box>
    </Container>
  );
}; 