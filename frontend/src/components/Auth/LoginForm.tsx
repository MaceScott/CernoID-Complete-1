import React, { useState, useEffect, useRef } from 'react';
import { Box, Button, TextField, Typography, Link, CircularProgress } from '@mui/material';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { FaceRecognition } from '@/components/face-recognition/FaceRecognition';

interface LoginFormData {
  email: string;
  password: string;
}

export const LoginForm = () => {
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
  });
  const { login, loginWithFace, isLoading, error } = useAuth();
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    // Start face recognition immediately
    startFaceRecognition();
  }, []);

  const startFaceRecognition = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (error) {
      console.error('Error accessing camera:', error);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(formData);
      router.push('/dashboard');
    } catch (err) {
      console.error('Login failed:', err);
    }
  };

  const handleFaceLogin = async (faceImage: Blob) => {
    try {
      await loginWithFace(faceImage);
      router.push('/dashboard');
    } catch (err) {
      console.error('Face login failed:', err);
    }
  };

  return (
    <Box sx={{ maxWidth: 400, mx: 'auto', p: 3 }}>
      <Typography variant="h4" align="center" gutterBottom>
        Login
      </Typography>
      
      <FaceRecognition onFaceDetected={handleFaceLogin} />

      <Typography variant="h6" align="center" sx={{ mt: 4, mb: 2 }}>
        Or login with credentials
      </Typography>

      {error && (
        <Typography color="error" align="center" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <form onSubmit={handleSubmit}>
        <TextField
          name="email"
          label="Email"
          type="email"
          fullWidth
          margin="normal"
          value={formData.email}
          onChange={handleChange}
          required
        />
        
        <TextField
          name="password"
          label="Password"
          type="password"
          fullWidth
          margin="normal"
          value={formData.password}
          onChange={handleChange}
          required
        />

        <Link
          href="/auth/forgot-password"
          sx={{
            display: 'block',
            textAlign: 'right',
            mb: 2,
            color: 'primary.main',
            '&:hover': {
              textDecoration: 'underline'
            }
          }}
        >
          Forgot Password?
        </Link>

        <Button
          type="submit"
          variant="contained"
          fullWidth
          disabled={isLoading}
          sx={{ mt: 2 }}
        >
          {isLoading ? <CircularProgress size={24} /> : 'Login'}
        </Button>
      </form>
    </Box>
  );
}; 
