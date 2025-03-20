"use client"

import { useState } from 'react';
import { Box, Typography, LinearProgress, Button } from '@mui/material';
import { RecognitionClient } from '../core/RecognitionClient';
import { FaceDetectionResult } from '../types';

interface FaceRegistrationProps {
  onComplete: (faceData: FormData[]) => void;
  onError: (error: Error) => void;
  requiredSamples?: number;
}

export function FaceRegistration({
  onComplete,
  onError,
  requiredSamples = 3
}: FaceRegistrationProps) {
  const [samples, setSamples] = useState<FormData[]>([]);
  const progress = (samples.length / requiredSamples) * 100;

  const handleCapture = (faceData: FormData) => {
    const newSamples = [...samples, faceData];
    setSamples(newSamples);

    if (newSamples.length >= requiredSamples) {
      onComplete(newSamples);
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Face Registration
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        We'll need to capture multiple images of your face from different angles for better recognition.
        Please follow the instructions and maintain good lighting conditions.
      </Typography>

      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Progress: {samples.length} of {requiredSamples} samples
        </Typography>
        <LinearProgress variant="determinate" value={progress} />
      </Box>

      <RecognitionClient
        onCapture={handleCapture}
        onError={onError}
        showResults={true}
        recognitionOptions={{
          minConfidence: 0.8,
          enableLandmarks: true,
          enableDescriptors: true
        }}
      />

      {samples.length > 0 && samples.length < requiredSamples && (
        <Typography variant="body2" color="primary" sx={{ mt: 2 }}>
          Great! Now please slightly turn your head and capture another sample.
        </Typography>
      )}
    </Box>
  );
} 