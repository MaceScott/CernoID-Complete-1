'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';

interface VideoStreamProps {
  streamUrl: string;
  cameraId: string;
  onError?: (error: Error) => void;
  quality?: 'low' | 'medium' | 'high';
  autoReconnect?: boolean;
  showStats?: boolean;
}

interface StreamStats {
  bitrate: number;
  fps: number;
  latency: number;
}

export default function VideoStream({
  streamUrl,
  cameraId,
  onError,
  quality = 'medium',
  autoReconnect = true,
  showStats = false,
}: VideoStreamProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<StreamStats | null>(null);
  const theme = useTheme();

  const qualitySettings = {
    low: { maxBitrate: 500000, maxFrameRate: 15 },
    medium: { maxBitrate: 1000000, maxFrameRate: 24 },
    high: { maxBitrate: 2500000, maxFrameRate: 30 },
  };

  const initializeWebRTC = useCallback(async () => {
    try {
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
      });

      // Set quality constraints
      const settings = qualitySettings[quality];
      const encodingParams = {
        maxBitrate: settings.maxBitrate,
        maxFramerate: settings.maxFrameRate,
      };

      pc.addTransceiver('video', {
        direction: 'recvonly',
        sendEncodings: [encodingParams],
      });

      // Handle ICE candidate events
      pc.onicecandidate = (event) => {
        if (event.candidate) {
          // Send candidate to signaling server
          fetch(`/api/cameras/${cameraId}/ice`, {
            method: 'POST',
            body: JSON.stringify(event.candidate),
          });
        }
      };

      // Handle incoming stream
      pc.ontrack = (event) => {
        if (videoRef.current && event.streams[0]) {
          videoRef.current.srcObject = event.streams[0];
          setLoading(false);
        }
      };

      // Create and send offer
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const response = await fetch(`/api/cameras/${cameraId}/offer`, {
        method: 'POST',
        body: JSON.stringify(offer),
      });

      const answer = await response.json();
      await pc.setRemoteDescription(new RTCSessionDescription(answer));

      peerConnectionRef.current = pc;

      // Start stats collection if enabled
      if (showStats) {
        collectStats();
      }
    } catch (err) {
      console.error('WebRTC initialization error:', err);
      setError('Failed to initialize video stream');
      onError?.(err as Error);
    }
  }, [cameraId, quality, showStats, onError]);

  const collectStats = useCallback(async () => {
    if (!peerConnectionRef.current) return;

    const statsInterval = setInterval(async () => {
      try {
        const stats = await peerConnectionRef.current?.getStats();
        if (!stats) return;

        let videoStats: StreamStats = {
          bitrate: 0,
          fps: 0,
          latency: 0,
        };

        stats.forEach((report) => {
          if (report.type === 'inbound-rtp' && report.kind === 'video') {
            videoStats.bitrate = report.bytesReceived * 8 / 1000; // kbps
            videoStats.fps = report.framesPerSecond || 0;
          }
          if (report.type === 'candidate-pair' && report.state === 'succeeded') {
            videoStats.latency = report.currentRoundTripTime * 1000; // ms
          }
        });

        setStats(videoStats);
      } catch (error) {
        console.error('Error collecting stats:', error);
      }
    }, 1000);

    return () => clearInterval(statsInterval);
  }, []);

  useEffect(() => {
    initializeWebRTC();

    return () => {
      if (peerConnectionRef.current) {
        peerConnectionRef.current.close();
      }
    };
  }, [initializeWebRTC]);

  // Auto-reconnect logic
  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout;

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && autoReconnect) {
        initializeWebRTC();
      }
    };

    const handleConnectionError = () => {
      if (autoReconnect) {
        reconnectTimeout = setTimeout(() => {
          initializeWebRTC();
        }, 5000);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('online', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('online', handleVisibilityChange);
      clearTimeout(reconnectTimeout);
    };
  }, [autoReconnect, initializeWebRTC]);

  if (error) {
    return (
      <Box
        sx={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: theme.palette.error.main,
          color: theme.palette.error.contrastText,
          padding: 2,
          borderRadius: 1,
        }}
      >
        <Typography variant="body2">{error}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ position: 'relative', width: '100%', height: '100%' }}>
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
        }}
      />
      {loading && (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
          }}
        >
          <CircularProgress />
        </Box>
      )}
      {showStats && stats && (
        <Box
          sx={{
            position: 'absolute',
            bottom: 8,
            left: 8,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            padding: 1,
            borderRadius: 1,
            fontSize: '0.75rem',
          }}
        >
          <Typography variant="caption" component="div">
            Bitrate: {Math.round(stats.bitrate)} kbps
          </Typography>
          <Typography variant="caption" component="div">
            FPS: {Math.round(stats.fps)}
          </Typography>
          <Typography variant="caption" component="div">
            Latency: {Math.round(stats.latency)} ms
          </Typography>
        </Box>
      )}
    </Box>
  );
} 