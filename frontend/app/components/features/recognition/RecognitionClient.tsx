'use client';

import React, { useRef, useEffect, useState } from 'react';
import { Box, Button, Typography } from '@mui/material';
import { FaceDetectionResult, RecognitionOptions } from '@/types/recognition';
import { captureFrame } from './core';

interface RecognitionClientProps {
  title: string;
  description: string;
  onCapture: (faceData: FormData) => void;
  onError: (error: Error) => void;
  showResults?: boolean;
  showControls?: boolean;
  recognitionOptions?: RecognitionOptions;
}

const defaultOptions: RecognitionOptions = {
  confidenceThreshold: 0.8,
  detectLandmarks: true,
  extractDescriptor: true
};

export const RecognitionClient: React.FC<RecognitionClientProps> = ({
  title,
  description,
  onCapture,
  onError,
  showResults = false,
  showControls = true,
  recognitionOptions
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [detectionResult, setDetectionResult] = useState<FaceDetectionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleError = (error: Error) => {
    setError(error.message);
    onError?.(error);
  };

  const startVideo = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user' }
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsStreaming(true);
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to access camera');
      handleError(error);
    }
  };

  const stopVideo = () => {
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
      setIsStreaming(false);
    }
  };

  const handleCapture = async () => {
    try {
      const canvas = canvasRef.current;
      const video = videoRef.current;

      if (!canvas || !video || !detectionResult) {
        handleError(new Error('Failed to capture image: missing required elements'));
        return;
      }

      const blob = await captureFrame(video, detectionResult);
      const formData = new FormData();
      formData.append('image', blob, 'face.jpg');

      onCapture?.(formData);
    } catch (err) {
      handleError(err instanceof Error ? err : new Error('Failed to capture image'));
    }
  };

  useEffect(() => {
    return () => {
      stopVideo();
    };
  }, []);

  return (
    <Box sx={{ width: '100%', maxWidth: 600, mx: 'auto', p: 2 }}>
      <Typography variant="h5" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body1" gutterBottom>
        {description}
      </Typography>

      <Box sx={{ position: 'relative', width: '100%', aspectRatio: '4/3', mb: 2 }}>
        <video
          ref={videoRef}
          autoPlay
          playsInline
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
        <canvas
          ref={canvasRef}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover'
          }}
        />
      </Box>

      {showControls && (
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={isStreaming ? stopVideo : startVideo}
          >
            {isStreaming ? 'Stop Camera' : 'Start Camera'}
          </Button>
          {isStreaming && (
            <Button
              variant="contained"
              color="primary"
              onClick={handleCapture}
            >
              Capture
            </Button>
          )}
        </Box>
      )}

      {error && (
        <Typography color="error" gutterBottom>
          {error}
        </Typography>
      )}
    </Box>
  );
}; 