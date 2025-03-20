"use client"

import { Box, Typography } from '@mui/material';
import { RecognitionClient } from '../core/RecognitionClient';

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
          minConfidence: 0.8,
          enableLandmarks: true,
          enableDescriptors: true
        }}
      />
    </Box>
  );
} 