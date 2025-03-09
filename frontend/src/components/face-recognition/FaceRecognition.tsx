import React, { useEffect, useRef, useState } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '@/hooks/useAuth';

interface FaceRecognitionProps {
  onFaceDetected: (faceImage: Blob) => Promise<void>;
}

export const FaceRecognition: React.FC<FaceRecognitionProps> = ({ onFaceDetected }) => {
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

  const captureFrame = (): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      if (!videoRef.current || !canvasRef.current) {
        reject('Video or canvas not initialized');
        return;
      }

      const canvas = canvasRef.current;
      const video = videoRef.current;
      const context = canvas.getContext('2d');

      if (!context) {
        reject('Could not get canvas context');
        return;
      }

      // Set canvas dimensions to match video
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Draw the current video frame
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert the frame to a blob
      canvas.toBlob((blob) => {
        if (blob) {
          resolve(blob);
        } else {
          reject('Failed to capture frame');
        }
      }, 'image/jpeg', 0.95);
    });
  };

  const detectFace = async () => {
    if (isLoading) return;

    try {
      setIsLoading(true);
      const frameBlob = await captureFrame();
      await onFaceDetected(frameBlob);
    } catch (error) {
      console.error('Face detection error:', error);
      setError('Failed to detect face. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box sx={{ position: 'relative', width: '100%', maxWidth: 640, mx: 'auto', mb: 4 }}>
      <video
        ref={videoRef}
        style={{
          width: '100%',
          borderRadius: 8,
          display: error ? 'none' : 'block'
        }}
        autoPlay
        playsInline
        muted
      />
      <canvas
        ref={canvasRef}
        style={{ display: 'none' }}
      />
      {isLoading && (
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 2
          }}
        >
          <CircularProgress />
          <Typography>Verifying face...</Typography>
        </Box>
      )}
      {error && (
        <Typography color="error" align="center" sx={{ mt: 2 }}>
          {error}
        </Typography>
      )}
    </Box>
  );
}; 