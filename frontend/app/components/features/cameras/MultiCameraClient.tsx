'use client';

import { useEffect, useState, useRef } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  IconButton,
  Dialog,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Fullscreen as FullscreenIcon,
  FilterAlt as FilterIcon,
  CheckCircle as OnlineIcon,
  Error as OfflineIcon
} from '@mui/icons-material';
import { useAuth } from '@/hooks/useAuth';
import { BaseFrame } from '@/desktop/BaseFrame';

interface Camera {
  id: string;
  name: string;
  type: 'facial' | 'security';
  status: 'online' | 'offline';
  stream: MediaStream | null;
}

export function MultiCameraClient() {
  const { user } = useAuth();
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'facial' | 'security'>('all');
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);

  // Add refs for video elements
  const videoRefs = useRef<{ [key: string]: HTMLVideoElement | null }>({});
  const fullscreenVideoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    fetchCameras();
    return () => {
      // Cleanup camera streams
      cameras.forEach(camera => {
        if (camera.stream) {
          camera.stream.getTracks().forEach(track => track.stop());
        }
      });
    };
  }, []);

  // Update video srcObject when stream changes
  useEffect(() => {
    cameras.forEach(camera => {
      const videoElement = videoRefs.current[camera.id];
      if (videoElement && camera.stream) {
        videoElement.srcObject = camera.stream;
      }
    });
  }, [cameras]);

  // Update fullscreen video srcObject
  useEffect(() => {
    if (fullscreenVideoRef.current && selectedCamera?.stream) {
      fullscreenVideoRef.current.srcObject = selectedCamera.stream;
    }
  }, [selectedCamera]);

  const fetchCameras = async () => {
    try {
      setLoading(true);
      // In a real app, this would be an API call
      const mockCameras: Camera[] = [
        { id: '1', name: 'Main Entrance', type: 'facial', status: 'online', stream: null },
        { id: '2', name: 'Side Door', type: 'security', status: 'online', stream: null },
        { id: '3', name: 'Reception', type: 'facial', status: 'online', stream: null },
        { id: '4', name: 'Parking Lot', type: 'security', status: 'offline', stream: null }
      ];
      setCameras(mockCameras);
      
      // Start streams for online cameras
      for (const camera of mockCameras) {
        if (camera.status === 'online') {
          try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            setCameras(prev => 
              prev.map(c => 
                c.id === camera.id ? { ...c, stream } : c
              )
            );
          } catch (err) {
            console.error(`Failed to start stream for camera ${camera.id}:`, err);
          }
        }
      }
    } catch (err) {
      setError('Failed to fetch cameras');
    } finally {
      setLoading(false);
    }
  };

  const filteredCameras = cameras.filter(camera => {
    if (filter === 'all') return true;
    return camera.type === filter;
  });

  return (
    <BaseFrame title="Multi-Camera View">
      <Container maxWidth="xl">
        <Box sx={{ mt: 4 }}>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 3 
          }}>
            <Typography variant="h4" component="h1">
              Camera Feeds
            </Typography>
            
            <ToggleButtonGroup
              value={filter}
              exclusive
              onChange={(_, value) => value && setFilter(value)}
              size="small"
            >
              <ToggleButton value="all">
                All Cameras
              </ToggleButton>
              <ToggleButton value="facial">
                Facial Recognition
              </ToggleButton>
              <ToggleButton value="security">
                Security Only
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>

          {loading ? (
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center',
              height: 400 
            }}>
              <CircularProgress />
            </Box>
          ) : error ? (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          ) : (
            <Grid container spacing={3}>
              {filteredCameras.map(camera => (
                <Grid item xs={12} sm={6} md={4} key={camera.id}>
                  <Paper 
                    sx={{ 
                      p: 2,
                      position: 'relative',
                      '&:hover .camera-controls': {
                        opacity: 1
                      }
                    }}
                  >
                    <Box sx={{ 
                      display: 'flex', 
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 1
                    }}>
                      <Typography variant="h6">
                        {camera.name}
                      </Typography>
                      {camera.status === 'online' ? (
                        <OnlineIcon color="success" />
                      ) : (
                        <OfflineIcon color="error" />
                      )}
                    </Box>
                    
                    <Box sx={{ 
                      width: '100%',
                      height: 200,
                      bgcolor: 'black',
                      position: 'relative'
                    }}>
                      {camera.status === 'online' ? (
                        <>
                          <video
                            ref={el => {
                              videoRefs.current[camera.id] = el;
                            }}
                            autoPlay
                            playsInline
                            muted
                            style={{
                              width: '100%',
                              height: '100%',
                              objectFit: 'cover'
                            }}
                          />
                          <Box 
                            className="camera-controls"
                            sx={{
                              position: 'absolute',
                              top: 0,
                              right: 0,
                              p: 1,
                              opacity: 0,
                              transition: 'opacity 0.2s',
                              bgcolor: 'rgba(0,0,0,0.5)'
                            }}
                          >
                            <IconButton
                              size="small"
                              sx={{ color: 'white' }}
                              onClick={() => setSelectedCamera(camera)}
                            >
                              <FullscreenIcon />
                            </IconButton>
                          </Box>
                        </>
                      ) : (
                        <Box sx={{
                          height: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}>
                          <Typography color="error">
                            Camera Offline
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          )}
        </Box>

        {/* Fullscreen Camera Dialog */}
        <Dialog
          fullScreen
          open={!!selectedCamera}
          onClose={() => setSelectedCamera(null)}
        >
          {selectedCamera && (
            <Box sx={{ height: '100%', bgcolor: 'black' }}>
              <Box sx={{ 
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                p: 2,
                bgcolor: 'rgba(0,0,0,0.5)',
                color: 'white',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <Typography variant="h6">
                  {selectedCamera.name}
                </Typography>
                <IconButton
                  color="inherit"
                  onClick={() => setSelectedCamera(null)}
                >
                  <FullscreenIcon />
                </IconButton>
              </Box>
              <video
                ref={fullscreenVideoRef}
                autoPlay
                playsInline
                muted
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain'
                }}
              />
            </Box>
          )}
        </Dialog>
      </Container>
    </BaseFrame>
  );
} 