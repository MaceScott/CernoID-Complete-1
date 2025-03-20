'use client';

import { Box } from '@mui/material';
import { RecognitionClient } from '../features/recognition/RecognitionClient';

interface AuthFaceRecognitionProps {
  onSuccess: (faceData: FormData) => void;
  onError: (error: Error) => void;
}

export function AuthFaceRecognition({ onSuccess, onError }: AuthFaceRecognitionProps) {
  return (
    <Box sx={{ maxWidth: 'sm', mx: 'auto', p: 2 }}>
      <RecognitionClient
        title="Face Recognition Login"
        description="Please look directly at the camera for face recognition. Make sure your face is well-lit and centered in the frame."
        onCapture={onSuccess}
        onError={onError}
        showResults={false}
        showControls={false}
        recognitionOptions={{
          minConfidence: 0.7,
          enableLandmarks: true,
          enableDescriptors: true
        }}
      />
    </Box>
  );
} 