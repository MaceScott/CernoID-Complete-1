"use client";

import React from 'react';
import { useEffect, useState } from 'react';
import { Grid, Paper } from '@mui/material';
import { CameraFeed } from './CameraFeed';
import { useWebSocketContext } from '@/providers/WebSocketProvider';
import { CameraConfig } from '@/types';

interface CameraGridProps {
  cameras: CameraConfig[];
}

type CameraStatus = CameraConfig['status'];

export function CameraGrid({ cameras }: CameraGridProps) {
  const [cameraStatuses, setCameraStatuses] = useState<Record<string, CameraStatus>>({});
  const { state, send } = useWebSocketContext();

  useEffect(() => {
    if (state.connected) {
      // Subscribe to camera status updates
      send({ type: 'subscribe', payload: { event: 'camera_status' } });
    }
  }, [state.connected, send]);

  useEffect(() => {
    const handleCameraStatus = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'camera_status') {
          const status = data.payload.status as CameraStatus;
          setCameraStatuses(prev => ({
            ...prev,
            [data.payload.id]: status
          }));
        }
      } catch (error) {
        console.error('Failed to parse camera status update:', error);
      }
    };

    // Add event listener
    window.addEventListener('message', handleCameraStatus);

    return () => {
      window.removeEventListener('message', handleCameraStatus);
    };
  }, []);

  return (
    <Grid container spacing={2}>
      {cameras.map(camera => (
        <Grid item xs={12} sm={6} md={4} key={camera.id}>
          <CameraFeed
            camera={camera}
            status={cameraStatuses[camera.id] || camera.status}
          />
        </Grid>
      ))}
    </Grid>
  );
}
