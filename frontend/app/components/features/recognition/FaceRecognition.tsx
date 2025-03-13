import React, { useEffect, useRef, useState } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '@/hooks/useAuth';

interface FaceRecognitionProps {
  onFaceDetected: (faceImage: Blob) => Promise<void>;
}

export const FaceRecognition = ({ onFaceDetected }: FaceRecognitionProps): JSX.Element => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, []);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: 640,
          height: 480,
          facingMode: 'user'
        } 
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        // Start face detection after camera is ready
        setTimeout(detectFace, 1000);
      }
    } catch (error) {
      setError('Error accessing camera. Please ensure camera permissions are granted.');
      console.error('Error accessing camera:', error);
    }
  };

  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
    }
  };

  const captureFrame = async (): Promise<Blob> => {
    if (!videoRef.current || !canvasRef.current) {
      throw new Error('Video or canvas reference not available');
    }

    const canvas = canvasRef.current;
    const video = videoRef.current;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      throw new Error('Could not get canvas context');
    }
    
    ctx.drawImage(video, 0, 0);
    
    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        if (!blob) {
          throw new Error('Failed to capture frame');
        }
        resolve(blob);
      }, 'image/jpeg');
    });
  };

  const detectFace = async () => {
    if (!videoRef.current?.srcObject) return;
    
    try {
      setIsLoading(true);
      const frameBlob = await captureFrame();
      await onFaceDetected(frameBlob);
    } catch (error) {
      setError('Error detecting face. Please try again.');
      console.error('Face detection error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box sx={{ position: 'relative', width: '100%', height: '100%' }}>
      <video
        ref={videoRef}
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        muted
        playsInline
      />
      <canvas
        ref={canvasRef}
        style={{ display: 'none' }}
      />
      {isLoading && (
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)'
        }}>
          <CircularProgress />
        </Box>
      )}
      {error && (
        <Typography color="error" sx={{ mt: 2 }}>
          {error}
        </Typography>
      )}
    </Box>
  );
}; 