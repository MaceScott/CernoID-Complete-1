"use client"

import { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  CircularProgress
} from '@mui/material';
import { RecognitionClient } from '../core/RecognitionClient';
import { FaceDetectionResult } from '..';

interface FaceComparisonProps {
  onCompare?: (similarity: number) => void;
  onError?: (error: Error) => void;
}

export function FaceComparison({
  onCompare,
  onError
}: FaceComparisonProps) {
  const [firstFace, setFirstFace] = useState<FaceDetectionResult | null>(null);
  const [secondFace, setSecondFace] = useState<FaceDetectionResult | null>(null);
  const [similarity, setSimilarity] = useState<number | null>(null);
  const [isComparing, setIsComparing] = useState(false);

  const handleFirstCapture = (faceData: FormData) => {
    // In a real implementation, this would extract the face descriptor from the FormData
    // For now, we'll simulate it
    const mockDescriptor = new Float32Array(128);
    setFirstFace({
      id: '1',
      confidence: 0.95,
      box: { x: 0, y: 0, width: 100, height: 100 },
      descriptor: mockDescriptor
    });
  };

  const handleSecondCapture = (faceData: FormData) => {
    // Similar mock implementation
    const mockDescriptor = new Float32Array(128);
    setSecondFace({
      id: '2',
      confidence: 0.95,
      box: { x: 0, y: 0, width: 100, height: 100 },
      descriptor: mockDescriptor
    });
  };

  const compareFaces = async () => {
    if (!firstFace?.descriptor || !secondFace?.descriptor) return;

    setIsComparing(true);
    try {
      // In a real implementation, this would calculate the actual similarity
      // For now, we'll simulate a comparison
      const mockSimilarity = Math.random() * 0.3 + 0.7; // Random value between 0.7 and 1.0
      setSimilarity(mockSimilarity);
      if (onCompare) onCompare(mockSimilarity);
    } catch (error) {
      if (onError) onError(error as Error);
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Face Comparison
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                First Face
              </Typography>
              <RecognitionClient
                onCapture={handleFirstCapture}
                onError={onError}
                showResults={true}
                recognitionOptions={{
                  minConfidence: 0.8,
                  enableDescriptors: true
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Second Face
              </Typography>
              <RecognitionClient
                onCapture={handleSecondCapture}
                onError={onError}
                showResults={true}
                recognitionOptions={{
                  minConfidence: 0.8,
                  enableDescriptors: true
                }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 2 }}>
        <Button
          variant="contained"
          onClick={compareFaces}
          disabled={!firstFace || !secondFace || isComparing}
        >
          {isComparing ? <CircularProgress size={24} /> : 'Compare Faces'}
        </Button>
      </Box>

      {similarity !== null && (
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Comparison Results
            </Typography>
            <Typography variant="body1">
              Similarity Score: {(similarity * 100).toFixed(1)}%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {similarity > 0.8
                ? 'High confidence match'
                : similarity > 0.6
                ? 'Possible match'
                : 'No match'}
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
} 