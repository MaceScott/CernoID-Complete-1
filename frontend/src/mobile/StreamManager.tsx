import React, { useEffect, useRef, useState } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

interface StreamConfig {
  quality: number;
  maxFps: number;
  resolution: [number, number];
  format: string;
}

interface StreamManagerProps {
  cameraId: number;
  onError?: (error: Error) => void;
}

export const StreamManager: React.FC<StreamManagerProps> = ({
  cameraId,
  onError
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);

  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket(`ws://localhost:8000/api/mobile/stream/${cameraId}`);

      ws.onopen = () => {
        setLoading(false);
        setError(null);
      };

      ws.onmessage = (event) => {
        if (imageRef.current && event.data instanceof Blob) {
          const url = URL.createObjectURL(event.data);
          imageRef.current.src = url;
          // Clean up old URLs
          setTimeout(() => URL.revokeObjectURL(url), 1000);
        }
      };

      ws.onerror = (event) => {
        const error = new Error('WebSocket error');
        setError(error.message);
        onError?.(error);
      };

      ws.onclose = () => {
        setError('Stream connection closed');
        // Attempt to reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };

      wsRef.current = ws;
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [cameraId, onError]);

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100%',
          minHeight: 200
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100%',
          minHeight: 200,
          bgcolor: 'error.light',
          color: 'error.contrastText',
          p: 2
        }}
      >
        <Typography>{error}</Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        height: '100%',
        minHeight: 200,
        bgcolor: 'background.paper'
      }}
    >
      <img
        ref={imageRef}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain'
        }}
        alt="Camera Stream"
      />
    </Box>
  );
}; 