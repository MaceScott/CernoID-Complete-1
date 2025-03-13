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
  Alert,
  Snackbar,
  Menu,
  MenuItem,
  Badge,
  Tooltip,
  Chip,
} from '@mui/material';
import {
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
  FilterAlt as FilterIcon,
  CheckCircle as OnlineIcon,
  Error as OfflineIcon,
  GridView as GridViewIcon,
  ViewStream as SingleViewIcon,
  Face as FaceIcon,
  Warning as WarningIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { useAuth } from '@/hooks/useAuth';
import { BaseFrame } from '@/desktop/BaseFrame';
import { motion, AnimatePresence } from 'framer-motion';

const MotionPaper = motion(Paper);

interface Camera {
  id: string;
  name: string;
  type: 'facial' | 'security';
  status: 'online' | 'offline';
  stream: MediaStream | null;
  facesDetected: number;
  unknownFaces: number;
  lastAlert?: string;
}

interface FaceDetection {
  id: string;
  name: string | null;
  confidence: number;
  boundingBox: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export function MultiCameraClient() {
  const { user } = useAuth();
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'facial' | 'security'>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'single'>('grid');
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);
  const [alert, setAlert] = useState<{ message: string; severity: 'warning' | 'error' } | null>(null);
  const videoRefs = useRef<{ [key: string]: HTMLVideoElement | null }>({});
  const canvasRefs = useRef<{ [key: string]: HTMLCanvasElement | null }>({});
  const [faceDetections, setFaceDetections] = useState<{ [key: string]: FaceDetection[] }>({});

  const filteredCameras = cameras.filter(camera => {
    if (filter === 'all') return true;
    return camera.type === filter;
  });

  useEffect(() => {
    const fetchCameras = async () => {
      try {
        const response = await fetch('/api/cameras');
        if (!response.ok) throw new Error('Failed to fetch cameras');
        const data = await response.json();
        setCameras(data);
      } catch (err) {
        setError('Failed to load cameras. Please try again.');
        console.error('Camera fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCameras();
  }, []);

  useEffect(() => {
    // WebSocket connection for real-time updates
    const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'face_detection') {
        setFaceDetections(prev => ({
          ...prev,
          [data.cameraId]: data.faces
        }));

        // Check for unknown faces
        const unknownFaces = data.faces.filter((face: FaceDetection) => !face.name);
        if (unknownFaces.length > 0) {
          setAlert({
            message: `Unknown face detected on camera ${data.cameraName}`,
            severity: 'warning'
          });
        }
      }
    };

    return () => ws.close();
  }, []);

  const handleViewModeChange = (mode: 'grid' | 'single') => {
    setViewMode(mode);
    if (mode === 'grid') {
      setSelectedCamera(null);
    }
  };

  const renderFaceDetections = (cameraId: string, video: HTMLVideoElement) => {
    const canvas = canvasRefs.current[cameraId];
    if (!canvas || !video) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear previous drawings
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw face detection boxes
    const detections = faceDetections[cameraId] || [];
    detections.forEach(face => {
      const { x, y, width, height } = face.boundingBox;
      
      // Scale coordinates to match video display size
      const scaleX = video.clientWidth / video.videoWidth;
      const scaleY = video.clientHeight / video.videoHeight;

      ctx.strokeStyle = face.name ? '#4CAF50' : '#f44336';
      ctx.lineWidth = 2;
      ctx.strokeRect(
        x * scaleX,
        y * scaleY,
        width * scaleX,
        height * scaleY
      );

      // Draw name/status
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.fillRect(
        x * scaleX,
        (y + height) * scaleY,
        width * scaleX,
        20
      );
      ctx.fillStyle = '#ffffff';
      ctx.font = '12px Arial';
      ctx.fillText(
        face.name || 'Unknown',
        x * scaleX + 5,
        (y + height) * scaleY + 15
      );
    });
  };

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
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <ToggleButtonGroup
                value={viewMode}
                exclusive
                onChange={(_, value) => value && handleViewModeChange(value)}
                size="small"
              >
                <ToggleButton value="grid">
                  <Tooltip title="Grid View">
                    <GridViewIcon />
                  </Tooltip>
                </ToggleButton>
                <ToggleButton value="single">
                  <Tooltip title="Single View">
                    <SingleViewIcon />
                  </Tooltip>
                </ToggleButton>
              </ToggleButtonGroup>

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
              {(viewMode === 'single' && selectedCamera ? [selectedCamera] : filteredCameras).map(camera => (
                <Grid 
                  item 
                  xs={12} 
                  sm={viewMode === 'single' ? 12 : 6} 
                  md={viewMode === 'single' ? 12 : 4} 
                  key={camera.id}
                >
                  <MotionPaper 
                    layout
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3 }}
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
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {camera.type === 'facial' && (
                          <Tooltip title="Face Recognition Active">
                            <Badge badgeContent={camera.facesDetected} color="primary">
                              <FaceIcon color="action" />
                            </Badge>
                          </Tooltip>
                        )}
                        {camera.unknownFaces > 0 && (
                          <Tooltip title="Unknown Faces Detected">
                            <Badge badgeContent={camera.unknownFaces} color="error">
                              <WarningIcon color="error" />
                            </Badge>
                          </Tooltip>
                        )}
                        {camera.status === 'online' ? (
                          <Tooltip title="Camera Online">
                            <OnlineIcon color="success" />
                          </Tooltip>
                        ) : (
                          <Tooltip title="Camera Offline">
                            <OfflineIcon color="error" />
                          </Tooltip>
                        )}
                      </Box>
                    </Box>
                    
                    <Box sx={{ 
                      width: '100%',
                      height: viewMode === 'single' ? 600 : 200,
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
                          <canvas
                            ref={el => {
                              canvasRefs.current[camera.id] = el;
                            }}
                            style={{
                              position: 'absolute',
                              top: 0,
                              left: 0,
                              width: '100%',
                              height: '100%',
                              pointerEvents: 'none'
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
                              onClick={() => viewMode === 'single' 
                                ? handleViewModeChange('grid')
                                : setSelectedCamera(camera)
                              }
                            >
                              {viewMode === 'single' ? (
                                <FullscreenExitIcon />
                              ) : (
                                <FullscreenIcon />
                              )}
                            </IconButton>
                          </Box>
                        </>
                      ) : (
                        <Box sx={{
                          height: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'text.secondary'
                        }}>
                          <Typography>Camera Offline</Typography>
                        </Box>
                      )}
                    </Box>

                    {camera.lastAlert && (
                      <Alert 
                        severity="warning" 
                        sx={{ mt: 2 }}
                        action={
                          <IconButton
                            aria-label="close"
                            color="inherit"
                            size="small"
                            onClick={() => {
                              setCameras(prev => 
                                prev.map(cam => 
                                  cam.id === camera.id 
                                    ? { ...cam, lastAlert: undefined }
                                    : cam
                                )
                              );
                            }}
                          >
                            <CloseIcon fontSize="inherit" />
                          </IconButton>
                        }
                      >
                        {camera.lastAlert}
                      </Alert>
                    )}
                  </MotionPaper>
                </Grid>
              ))}
            </Grid>
          )}
        </Box>
      </Container>

      <Snackbar
        open={!!alert}
        autoHideDuration={6000}
        onClose={() => setAlert(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setAlert(null)} 
          severity={alert?.severity || 'info'}
          sx={{ width: '100%' }}
        >
          {alert?.message || ''}
        </Alert>
      </Snackbar>
    </BaseFrame>
  );
} 