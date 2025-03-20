'use client';

import { useState } from 'react';
import { Box, Button, Typography, CircularProgress } from '@mui/material';
import { RecognitionClient } from '../features/recognition/RecognitionClient';

interface FaceVerificationProps {
  onVerify: (faceData: FormData) => Promise<boolean>;
  onSuccess: () => void;
  onError: (error: Error) => void;
  maxAttempts?: number;
}

export function FaceVerification({
  onVerify,
  onSuccess,
  onError,
  maxAttempts = 3
}: FaceVerificationProps) {
  const [isVerifying, setIsVerifying] = useState(false);
  const [attempts, setAttempts] = useState(0);
  const [verificationError, setVerificationError] = useState<string | null>(null);

  const handleCapture = async (faceData: FormData) => {
    try {
      setIsVerifying(true);
      setVerificationError(null);
      
      const isVerified = await onVerify(faceData);
      
      if (isVerified) {
        onSuccess();
      } else {
        setAttempts(prev => prev + 1);
        if (attempts + 1 >= maxAttempts) {
          throw new Error('Maximum verification attempts reached');
        }
        setVerificationError('Face verification failed. Please try again.');
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Face verification failed');
      setVerificationError(error.message);
      onError(error);
    } finally {
      setIsVerifying(false);
    }
  };

  if (attempts >= maxAttempts) {
    return (
      <Box sx={{ textAlign: 'center', p: 2 }}>
        <Typography variant="h6" color="error" gutterBottom>
          Maximum Attempts Reached
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Please try again later or use an alternative authentication method.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 'sm', mx: 'auto', p: 2 }}>
      {isVerifying ? (
        <Box sx={{ textAlign: 'center', p: 4 }}>
          <CircularProgress />
          <Typography variant="body1" sx={{ mt: 2 }}>
            Verifying your face...
          </Typography>
        </Box>
      ) : (
        <>
          <RecognitionClient
            title="Face Verification"
            description="Please look directly at the camera and ensure good lighting for verification."
            onCapture={handleCapture}
            onError={onError}
            showResults={false}
            showControls={true}
            recognitionOptions={{
              minConfidence: 0.8,
              enableLandmarks: true,
              enableDescriptors: true
            }}
          />

          {verificationError && (
            <Typography
              variant="body2"
              color="error"
              align="center"
              sx={{ mt: 2 }}
            >
              {verificationError}
              {attempts < maxAttempts && (
                <Box component="span" sx={{ display: 'block' }}>
                  {maxAttempts - attempts} attempts remaining
                </Box>
              )}
            </Typography>
          )}
        </>
      )}
    </Box>
  );
} 