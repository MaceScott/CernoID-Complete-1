"use client"

import { Box } from '@mui/material';
import { Typography } from '@mui/material';
import { RecognitionClient } from '../core/RecognitionClient';
import { DEFAULT_RECOGNITION_OPTIONS } from '@/types/recognition';

interface FaceVerificationProps {
  onVerify: (faceData: FormData) => void;
  onError: (error: Error) => void;
  verificationContext?: string;
}

export function FaceVerification({
  onVerify,
  onError,
  verificationContext = 'identity verification'
}: FaceVerificationProps) {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Face Verification
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Please look at the camera for {verificationContext}.
        Ensure your face is well-lit and clearly visible.
      </Typography>

      <RecognitionClient
        onCapture={onVerify}
        onError={onError}
        showResults={true}
        recognitionOptions={{
          ...DEFAULT_RECOGNITION_OPTIONS,
          detectLandmarks: true,
          extractDescriptor: true
        }}
      />
    </Box>
  );
} 