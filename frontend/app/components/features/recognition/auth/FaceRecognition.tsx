"use client"

import { Box } from '@mui/material';
import { Typography } from '@mui/material';
import { RecognitionClient } from '../core/RecognitionClient';
import { DEFAULT_RECOGNITION_OPTIONS } from '@/types/recognition';

interface AuthFaceRecognitionProps {
  onSuccess: (faceData: FormData) => void;
  onError: (error: Error) => void;
}

export function AuthFaceRecognition({ onSuccess, onError }: AuthFaceRecognitionProps) {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Face Recognition Login
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Please look directly at the camera and ensure your face is well-lit.
      </Typography>
      
      <RecognitionClient
        onCapture={onSuccess}
        onError={onError}
        showResults={false}
        recognitionOptions={{
          ...DEFAULT_RECOGNITION_OPTIONS,
          detectLandmarks: true,
          extractDescriptor: true
        }}
      />
    </Box>
  );
} 