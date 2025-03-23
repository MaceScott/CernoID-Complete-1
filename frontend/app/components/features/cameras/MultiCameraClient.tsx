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
import { CameraConfig } from '@/types';

const MotionPaper = motion(Paper);

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
  const [cameras, setCameras] = useState<CameraConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'facial' | 'security'>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'single'>('grid');
  const [selectedCamera, setSelectedCamera] = useState<CameraConfig | null>(null);
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
    const wsUrl = typeof window !== 'undefined' ? window.location.origin.replace(/^http/, 'ws') : 'ws://localhost:8000/ws';
    const ws = new WebSocket(wsUrl);

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
                  md={viewMode === 'single' ? 12 : 6}
                  key={camera.id}
                >
                  <MotionPaper
                    elevation={3}
                    sx={{
                      position: 'relative',
                      overflow: 'hidden',
                      cursor: 'pointer',
                      '&:hover': {
                        transform: 'scale(1.02)',
                        transition: 'transform 0.2s ease-in-out'
                      }
                    }}
                    onClick={() => viewMode === 'grid' && setSelectedCamera(camera)}
                  >
                    <Box sx={{ position: 'relative', paddingTop: '56.25%' }}>
                      <video
                        ref={el => { videoRefs.current[camera.id] = el; }}
                        src={camera.streamUrl}
                        autoPlay
                        playsInline
                        muted
                        style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover'
                        }}
                        onLoadedMetadata={(e) => {
                          const video = e.target as HTMLVideoElement;
                          renderFaceDetections(camera.id, video);
                        }}
                      />
                      <canvas
                        ref={el => { canvasRefs.current[camera.id] = el; }}
                        style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          width: '100%',
                          height: '100%'
                        }}
                      />
                      <Box sx={{
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        display: 'flex',
                        gap: 1
                      }}>
                        <Chip
                          icon={camera.status === 'active' ? <OnlineIcon /> : <OfflineIcon />}
                          label={camera.status === 'active' ? 'Online' : 'Offline'}
                          color={camera.status === 'active' ? 'success' : 'error'}
                          size="small"
                        />
                        {camera.alerts && camera.alerts.length > 0 && (
                          <Chip
                            icon={<WarningIcon />}
                            label={`${camera.alerts.length} Alerts`}
                            color="warning"
                            size="small"
                          />
                        )}
                      </Box>
                    </Box>
                    <Box sx={{ p: 2 }}>
                      <Typography variant="h6" noWrap>
                        {camera.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" noWrap>
                        {camera.location || 'No location specified'}
                      </Typography>
                    </Box>
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