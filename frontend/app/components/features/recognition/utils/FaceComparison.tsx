"use client"

import { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Grid,
  Typography
} from '@mui/material';
import { RecognitionClient } from '../core/RecognitionClient';

interface FaceComparisonProps {
  onCompare?: (similarity: number) => void;
  onError?: (error: Error) => void;
}

export function FaceComparison({
  onCompare,
  onError
}: FaceComparisonProps) {
  const [firstFace, setFirstFace] = useState<FormData | null>(null);
  const [secondFace, setSecondFace] = useState<FormData | null>(null);
  const [similarity, setSimilarity] = useState<number | null>(null);
  const [isComparing, setIsComparing] = useState(false);

  const handleFirstCapture = (faceData: FormData) => {
    setFirstFace(faceData);
    setSimilarity(null);
  };

  const handleSecondCapture = (faceData: FormData) => {
    setSecondFace(faceData);
    setSimilarity(null);
  };

  const compareFaces = async () => {
    if (!firstFace || !secondFace) return;

    setIsComparing(true);
    try {
      const formData = new FormData();
      formData.append('face1', firstFace.get('face') as Blob);
      formData.append('face2', secondFace.get('face') as Blob);

      const response = await fetch('/api/recognition/compare', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Failed to compare faces');
      }

      const score = data.data.similarity;
      setSimilarity(score);
      onCompare?.(score);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <Box>
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
                  confidenceThreshold: 0.8,
                  detectLandmarks: true,
                  extractDescriptor: true
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
                  confidenceThreshold: 0.8,
                  detectLandmarks: true,
                  extractDescriptor: true
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