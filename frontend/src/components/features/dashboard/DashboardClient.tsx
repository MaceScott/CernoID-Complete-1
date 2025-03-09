'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { 
  Box, 
  Button, 
  Container, 
  Typography, 
  Grid, 
  Paper,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Videocam as VideocamIcon,
  Settings as SettingsIcon,
  SupervisorAccount as AdminIcon,
  Person as PersonIcon
} from '@mui/icons-material';

interface Log {
  id: string;
  timestamp: string;
  event: string;
  details: string;
}

export function DashboardClient() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recentLogs, setRecentLogs] = useState<Log[]>([]);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }

    // Start camera feed
    startCamera();

    // Fetch recent logs
    fetchRecentLogs();

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [user, router]);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setLoading(false);
    } catch (err) {
      setError('Failed to access camera');
      setLoading(false);
    }
  };

  const fetchRecentLogs = async () => {
    try {
      const response = await fetch('/api/logs/recent');
      const data = await response.json();
      setRecentLogs(data.logs);
    } catch (err) {
      console.error('Failed to fetch logs:', err);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Welcome, {user.name}!
        </Typography>

        <Grid container spacing={3}>
          {/* Main Camera Feed */}
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 2, height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Live Camera Feed
              </Typography>
              <Box sx={{ 
                width: '100%', 
                height: 400, 
                bgcolor: 'black',
                position: 'relative'
              }}>
                {loading ? (
                  <Box sx={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <CircularProgress />
                  </Box>
                ) : error ? (
                  <Alert severity="error" sx={{ m: 2 }}>
                    {error}
                  </Alert>
                ) : (
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover'
                    }}
                  />
                )}
              </Box>
            </Paper>
          </Grid>

          {/* Recent Logs */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              <List>
                {recentLogs.map(log => (
                  <ListItem key={log.id}>
                    <ListItemText
                      primary={log.event}
                      secondary={`${log.details} - ${new Date(log.timestamp).toLocaleString()}`}
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>

          {/* Navigation Buttons */}
          <Grid item xs={12}>
            <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                startIcon={<VideocamIcon />}
                onClick={() => router.push('/cameras')}
              >
                Multi-Camera View
              </Button>
              
              {user.role === 'admin' && (
                <Button
                  variant="contained"
                  startIcon={<AdminIcon />}
                  onClick={() => router.push('/admin')}
                >
                  Administrative
                </Button>
              )}
              
              <Button
                variant="contained"
                startIcon={<SettingsIcon />}
                onClick={() => router.push('/settings')}
              >
                System Settings
              </Button>
              
              <Button
                variant="contained"
                startIcon={<PersonIcon />}
                onClick={() => router.push('/recognition')}
              >
                Person Identification
              </Button>
              
              <Button
                variant="outlined"
                color="error"
                onClick={logout}
              >
                Logout
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
} 