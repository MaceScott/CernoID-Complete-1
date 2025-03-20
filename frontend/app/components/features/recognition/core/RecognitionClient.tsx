"use client"

import { Box } from '@mui/material';
import { RecognitionViewer } from './RecognitionViewer';
import { RecognitionOptions } from '../types';

interface RecognitionClientProps {
  onCapture?: (faceData: FormData) => void;
  onError?: (error: Error) => void;
  showResults?: boolean;
  showControls?: boolean;
  recognitionOptions?: RecognitionOptions;
}

export function RecognitionClient({
  onCapture,
  onError,
  showResults = true,
  showControls = true,
  recognitionOptions
}: RecognitionClientProps) {
  return (
    <Box sx={{ width: '100%', maxWidth: 800, mx: 'auto' }}>
      <RecognitionViewer
        onCapture={onCapture}
        onError={onError}
        showResults={showResults}
        showControls={showControls}
        recognitionOptions={recognitionOptions}
      />
    </Box>
  );
} 