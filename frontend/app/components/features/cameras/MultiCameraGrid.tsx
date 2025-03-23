'use client';

import React, { useState, useMemo } from 'react';
import { Grid, Paper, useTheme, Box } from '@mui/material';
import dynamic from 'next/dynamic';
import { useOptimizedQuery } from '@/hooks/useOptimizedQuery';
import { CameraConfig } from '@/types';

// Dynamically import the video stream component
const VideoStream = dynamic(() => import('./VideoStream'), {
  loading: () => (
    <Box
      sx={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.1)',
      }}
    >
      Loading...
    </Box>
  ),
  ssr: false, // Disable server-side rendering for video components
});

interface MultiCameraGridProps {
  layout?: '2x2' | '3x3' | '4x4';
  quality?: 'low' | 'medium' | 'high';
}

export default function MultiCameraGrid({
  layout = '2x2',
  quality = 'medium',
}: MultiCameraGridProps) {
  const theme = useTheme();
  const [visibleCameras, setVisibleCameras] = useState<Set<string>>(new Set());

  // Fetch cameras with optimized query hook
  const { data: cameras, isLoading, error } = useOptimizedQuery<CameraConfig[]>({
    key: 'cameras',
    fetchFn: async () => {
      const response = await fetch('/api/cameras');
      if (!response.ok) {
        throw new Error('Failed to fetch cameras');
      }
      return response.json();
    },
    staleTime: 60000, // Cache for 1 minute
  });

  // Calculate grid layout
  const gridConfig = useMemo(() => {
    const configs = {
      '2x2': { cols: 2, rows: 2 },
      '3x3': { cols: 3, rows: 3 },
      '4x4': { cols: 4, rows: 4 },
    };
    return configs[layout];
  }, [layout]);

  // Intersection Observer callback
  const handleIntersection = (cameraId: string) => (entries: IntersectionObserverEntry[]) => {
    entries.forEach((entry) => {
      setVisibleCameras((prev) => {
        const next = new Set(prev);
        if (entry.isIntersecting) {
          next.add(cameraId);
        } else {
          next.delete(cameraId);
        }
        return next;
      });
    });
  };

  // Set up Intersection Observer
  React.useEffect(() => {
    const observers: IntersectionObserver[] = [];
    const elements = document.querySelectorAll('.camera-container');

    elements.forEach((element) => {
      const cameraId = element.getAttribute('data-camera-id');
      if (cameraId) {
        const observer = new IntersectionObserver(handleIntersection(cameraId), {
          threshold: 0.5,
        });
        observer.observe(element);
        observers.push(observer);
      }
    });

    return () => {
      observers.forEach((observer) => observer.disconnect());
    };
  }, [cameras]);

  if (isLoading) {
    return <div>Loading cameras...</div>;
  }

  if (error) {
    return <div>Error loading cameras: {error.message}</div>;
  }

  return (
    <Grid container spacing={2}>
      {cameras?.map((camera, index) => (
        <Grid
          key={camera.id}
          item
          xs={12 / gridConfig.cols}
          sx={{
            aspectRatio: '16/9',
          }}
        >
          <Paper
            className="camera-container"
            data-camera-id={camera.id}
            sx={{
              height: '100%',
              overflow: 'hidden',
              position: 'relative',
              transition: theme.transitions.create(['transform', 'box-shadow'], {
                duration: theme.transitions.duration.standard,
              }),
              '&:hover': {
                transform: 'scale(1.02)',
                boxShadow: theme.shadows[8],
              },
            }}
          >
            {visibleCameras.has(camera.id) && (
              <VideoStream
                streamUrl={camera.streamUrl}
                cameraId={camera.id}
                quality={quality}
                autoReconnect
                showStats={false}
              />
            )}
          </Paper>
        </Grid>
      ))}
    </Grid>
  );
} 