'use client';

import React, { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { LoginData } from '@/types/auth';
import { Box, Button, Container, Paper, TextField, Typography } from '@mui/material';
import { useRouter } from 'next/navigation';

export const Login = () => {
  const { login, loginWithFace } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [credentials, setCredentials] = useState<LoginData>({
    email: '',
    password: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      await login(credentials);
      router.push('/dashboard');
    } catch (err) {
      setError('Login failed. Please check your credentials.');
    }
  };

  const handleFaceLogin = async () => {
    setError(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      const video = document.createElement('video');
      video.srcObject = stream;
      await video.play();

      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const context = canvas.getContext('2d');
      if (!context) throw new Error('Could not get canvas context');

      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      stream.getTracks().forEach(track => track.stop());

      const imageData = canvas.toDataURL('image/jpeg');
      await loginWithFace(imageData);
      router.push('/dashboard');
    } catch (err) {
      setError('Face login failed. Please try again or use email/password.');
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8 }}>
        <Paper sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            Login
          </Typography>
          {error && (
            <Typography color="error" align="center" gutterBottom>
              {error}
            </Typography>
          )}
          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              margin="normal"
              label="Email"
              name="email"
              type="email"
              value={credentials.email}
              onChange={handleInputChange}
              required
            />
            <TextField
              fullWidth
              margin="normal"
              label="Password"
              name="password"
              type="password"
              value={credentials.password}
              onChange={handleInputChange}
              required
            />
            <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button type="submit" variant="contained" color="primary" fullWidth>
                Login with Email
              </Button>
              <Button
                type="button"
                variant="outlined"
                color="primary"
                fullWidth
                onClick={handleFaceLogin}
              >
                Login with Face
              </Button>
            </Box>
          </form>
        </Paper>
      </Box>
    </Container>
  );
}; 