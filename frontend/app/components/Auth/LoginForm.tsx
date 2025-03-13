'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { LoginData } from '@/types/auth';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Box,
  Button,
  Paper,
  TextField,
  Typography,
  CircularProgress,
  Link as MuiLink,
} from '@mui/material';

export const LoginForm = () => {
  const { login, loginWithFace } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const formRef = useRef<HTMLFormElement>(null);
  const mounted = useRef(false);
  const [credentials, setCredentials] = useState<LoginData>({
    email: '',
    password: '',
  });

  const clearForm = () => {
    // Clear React state
    setCredentials({ email: '', password: '' });
    setError(null);
    setIsSubmitting(false);

    // Clear form inputs directly
    if (formRef.current) {
      const form = formRef.current;
      form.reset();
      
      // Clear all input fields
      const inputs = form.getElementsByTagName('input');
      for (let i = 0; i < inputs.length; i++) {
        const input = inputs[i];
        input.value = '';
        
        // Clear any browser-stored data
        input.setAttribute('autocomplete', 'off');
        input.setAttribute('data-form-type', 'other');
      }
    }

    // Force browser to forget stored values
    if (typeof window !== 'undefined') {
      window.history.replaceState({}, '', window.location.pathname);
    }
  };

  // Clear form on mount and when component is unmounted/remounted
  useEffect(() => {
    if (!mounted.current) {
      mounted.current = true;
      clearForm();
    }
    return () => {
      mounted.current = false;
      clearForm();
    };
  }, []);

  // Clear form on route change
  useEffect(() => {
    router.events?.on('routeChangeStart', clearForm);
    return () => {
      router.events?.off('routeChangeStart', clearForm);
    };
  }, [router]);

  // Clear form on visibility change and focus
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        clearForm();
      }
    };

    const handleFocus = () => {
      clearForm();
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);
    window.addEventListener('pageshow', (event) => {
      if (event.persisted) {
        clearForm();
      }
    });
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(credentials);
      clearForm();
      router.push('/dashboard');
    } catch (err) {
      setError('Login failed. Please check your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFaceLogin = async () => {
    setError(null);
    setIsSubmitting(true);

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
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        p: 4, 
        width: '100%',
        maxWidth: 400,
        borderRadius: 2,
        bgcolor: 'background.paper'
      }}
    >
      <form 
        ref={formRef} 
        onSubmit={handleSubmit} 
        autoComplete="off"
        onFocus={clearForm}
        data-form-type="other"
      >
        {/* Hidden fields to prevent autofill */}
        <input type="text" name="username" style={{ display: 'none' }} tabIndex={-1} />
        <input type="password" name="password" style={{ display: 'none' }} tabIndex={-1} />
        
        <TextField
          fullWidth
          margin="normal"
          label="Email"
          name="email"
          type="email"
          value={credentials.email}
          onChange={handleInputChange}
          required
          autoComplete="off"
          inputProps={{
            autoComplete: 'off',
            'data-form-type': 'other',
            autoFocus: false,
          }}
          sx={{ 
            mb: 2,
            '& .MuiInputLabel-root': {
              backgroundColor: 'background.paper',
              px: 1,
            }
          }}
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
          autoComplete="new-password"
          inputProps={{
            autoComplete: 'new-password',
            'data-form-type': 'other',
            autoFocus: false,
          }}
          sx={{ 
            mb: 3,
            '& .MuiInputLabel-root': {
              backgroundColor: 'background.paper',
              px: 1,
            }
          }}
        />

        {error && (
          <Typography color="error" variant="body2" sx={{ mb: 2, textAlign: 'center' }}>
            {error}
          </Typography>
        )}

        <Button
          fullWidth
          type="submit"
          variant="contained"
          disabled={isSubmitting}
          sx={{ mb: 2 }}
        >
          {isSubmitting ? <CircularProgress size={24} /> : 'Sign In'}
        </Button>

        <Button
          fullWidth
          variant="outlined"
          onClick={handleFaceLogin}
          disabled={isSubmitting}
          sx={{ mb: 2 }}
        >
          {isSubmitting ? <CircularProgress size={24} /> : 'Sign In with Face ID'}
        </Button>

        <Box sx={{ textAlign: 'center', mt: 2 }}>
          <Link href="/forgot-password" passHref>
            <MuiLink underline="hover">
              Forgot Password?
            </MuiLink>
          </Link>
        </Box>
      </form>
    </Paper>
  );
}; 