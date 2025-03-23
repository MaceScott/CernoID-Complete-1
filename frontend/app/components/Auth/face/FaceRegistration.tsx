'use client';

import { useState } from 'react';
import { Box, Button, Typography } from '@mui/material';
import { RecognitionClient } from '@/components/features/recognition/RecognitionClient';
import { FaceDetectionResult } from '@/types/recognition';

export interface FaceRegistrationProps {
  onSuccess?: () => void;
  onError: (error: Error) => void;
}

export function FaceRegistration({ onSuccess, onError }: FaceRegistrationProps) {
  const [isCapturing, setIsCapturing] = useState(false);
  const [capturedFaces, setCapturedFaces] = useState<FormData[]>([]);

  const handleCapture = async (faceData: FormData) => {
    try {
      setCapturedFaces(prev => [...prev, faceData]);
      if (capturedFaces.length >= 2) {
        setIsCapturing(false);
        // Registration successful
        onSuccess?.();
      }
    } catch (err) {
      onError(err instanceof Error ? err : new Error('Failed to register face'));
    }
  };

  return (
    <Box sx={{ maxWidth: 'sm', mx: 'auto', p: 2 }}>
      {!isCapturing ? (
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            Face Registration
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            We'll need to capture multiple images of your face from different angles for better recognition.
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => setIsCapturing(true)}
          >
            Start Face Registration
          </Button>
        </Box>
      ) : (
        <RecognitionClient
          title="Face Registration"
          description={`Please look ${capturedFaces.length === 0 ? 'straight ahead' : 'slightly to the side'} and ensure good lighting. Capture ${3 - capturedFaces.length} more ${capturedFaces.length === 2 ? 'image' : 'images'}.`}
          onCapture={handleCapture}
          onError={onError}
          showResults={true}
          showControls={true}
          recognitionOptions={{
            minConfidence: 0.8,
            enableLandmarks: true,
            enableDescriptors: true
          }}
        />
      )}

      {capturedFaces.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Captured {capturedFaces.length} of 3 images
          </Typography>
        </Box>
      )}
    </Box>
  );
} 