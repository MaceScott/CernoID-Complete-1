'use client';

import React, { useRef, useEffect, useState } from 'react';
import { Box, Button, Typography } from '@mui/material';
import { FaceDetectionResult } from '@/types/recognition';

interface RecognitionClientProps {
  title: string;
  description: string;
  onCapture: (faceData: FormData) => void;
  onError: (error: Error) => void;
  showResults?: boolean;
  showControls?: boolean;
  recognitionOptions?: {
    minConfidence: number;
    enableLandmarks: boolean;
    enableDescriptors: boolean;
  };
}

export const RecognitionClient: React.FC<RecognitionClientProps> = ({
  title,
  description,
  onCapture,
  onError,
  showResults = true,
  showControls = true,
  recognitionOptions = {
    minConfidence: 0.8,
    enableLandmarks: true,
    enableDescriptors: true
  }
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [detectionResult, setDetectionResult] = useState<FaceDetectionResult | null>(null);

  useEffect(() => {
    return () => {
      stopStream();
    };
  }, []);

  const startStream = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsStreaming(true);
    } catch (err) {
      onError(err instanceof Error ? err : new Error('Failed to access camera'));
    }
  };

  const stopStream = () => {
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
  };

  const captureImage = async () => {
    if (!videoRef.current || !isStreaming) return;

    try {
      const canvas = document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      canvas.getContext('2d')?.drawImage(videoRef.current, 0, 0);

      const blob = await new Promise<Blob>((resolve) => {
        canvas.toBlob((blob) => {
          if (blob) resolve(blob);
        }, 'image/jpeg', 0.95);
      });

      const formData = new FormData();
      formData.append('image', blob, 'face.jpg');

      onCapture(formData);
    } catch (err) {
      onError(err instanceof Error ? err : new Error('Failed to capture image'));
    }
  };

  return (
    <Box sx={{ maxWidth: 'sm', mx: 'auto', p: 2 }}>
      <Typography variant="h5" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        {description}
      </Typography>

      <Box sx={{ position: 'relative', width: '100%', aspectRatio: '4/3', mb: 2 }}>
        <video
          ref={videoRef}
          autoPlay
          playsInline
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            borderRadius: '8px',
            display: isStreaming ? 'block' : 'none'
          }}
        />
        {!isStreaming && (
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
              bgcolor: 'grey.100',
              borderRadius: '8px'
            }}
          >
            <Typography color="text.secondary">Camera not active</Typography>
          </Box>
        )}
      </Box>

      {showControls && (
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          {!isStreaming ? (
            <Button
              variant="contained"
              color="primary"
              onClick={startStream}
            >
              Start Camera
            </Button>
          ) : (
            <>
              <Button
                variant="contained"
                color="primary"
                onClick={captureImage}
              >
                Capture
              </Button>
              <Button
                variant="outlined"
                color="secondary"
                onClick={stopStream}
              >
                Stop Camera
              </Button>
            </>
          )}
        </Box>
      )}

      {showResults && detectionResult && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Confidence: {(detectionResult.confidence * 100).toFixed(1)}%
          </Typography>
        </Box>
      )}
    </Box>
  );
}; 