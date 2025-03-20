"use client"

import { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  styled
} from '@mui/material';
import { useFaceRecognition } from '@/hooks/useFaceRecognition';
import { FaceDetectionResult, RecognitionOptions, DEFAULT_RECOGNITION_OPTIONS } from '../types';
import { ResultsViewer } from './ResultsViewer';

interface RecognitionViewerProps {
  onCapture?: (faceData: FormData) => void;
  onError?: (error: Error) => void;
  showResults?: boolean;
  showControls?: boolean;
  recognitionOptions?: RecognitionOptions;
}

const StyledVideo = styled('video')({
  width: '100%',
  height: 'auto'
});

const StyledCanvas = styled('canvas')({
  position: 'absolute',
  top: 0,
  left: 0,
  width: '100%',
  height: '100%'
});

export function RecognitionViewer({
  onCapture,
  onError,
  showResults = true,
  showControls = true,
  recognitionOptions
}: RecognitionViewerProps) {
  const {
    videoRef,
    canvasRef,
    isInitialized,
    isLoading,
    error,
    startRecognition,
    stopRecognition
  } = useFaceRecognition({
    onCapture,
    onError,
    autoStart: !showControls,
    recognitionOptions: {
      ...DEFAULT_RECOGNITION_OPTIONS,
      ...recognitionOptions
    }
  });

  const [currentDetection, setCurrentDetection] = useState<FaceDetectionResult | null>(null);

  if (error) {
    return (
      <Card>
        <CardContent>
          <Typography color="error" gutterBottom>
            {error}
          </Typography>
          {showControls && (
            <Button
              color="primary"
              variant="contained"
              onClick={() => startRecognition()}
              sx={{ mt: 1 }}
            >
              Try Again
            </Button>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ position: 'relative', width: '100%', maxWidth: 640, mx: 'auto' }}>
            {isLoading && (
              <Box
                sx={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: 'rgba(0, 0, 0, 0.5)',
                  zIndex: 1
                }}
              >
                <Typography color="white">
                  Initializing camera...
                </Typography>
              </Box>
            )}
            <StyledVideo
              ref={videoRef}
              autoPlay
              playsInline
              muted
            />
            <StyledCanvas ref={canvasRef} />
          </Box>

          {showControls && (
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 2 }}>
              <Button
                color="primary"
                variant="contained"
                onClick={() => startRecognition()}
                disabled={isLoading || !isInitialized}
              >
                Start Recognition
              </Button>
              <Button
                color="primary"
                variant="outlined"
                onClick={() => stopRecognition()}
                disabled={isLoading || !isInitialized}
              >
                Stop Recognition
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>

      {showResults && currentDetection && (
        <ResultsViewer
          detection={currentDetection}
          showLandmarks={recognitionOptions?.enableLandmarks}
          showDescriptor={recognitionOptions?.enableDescriptors}
        />
      )}
    </Box>
  );
} 