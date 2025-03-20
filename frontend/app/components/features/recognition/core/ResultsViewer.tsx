"use client"

import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Stack
} from '@mui/material';
import { FaceDetectionResult } from '../types';

interface ResultsViewerProps {
  detection: FaceDetectionResult;
  showLandmarks?: boolean;
  showDescriptor?: boolean;
}

export function ResultsViewer({
  detection,
  showLandmarks = false,
  showDescriptor = false
}: ResultsViewerProps) {
  const confidencePercent = Math.round(detection.confidence * 100);
  const confidenceColor = confidencePercent > 80 ? 'success' : confidencePercent > 60 ? 'warning' : 'error';

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Detection Results
        </Typography>

        <Stack spacing={2}>
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Confidence Score
            </Typography>
            <Chip
              label={`${confidencePercent}%`}
              color={confidenceColor}
              variant="outlined"
            />
          </Box>

          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Bounding Box
            </Typography>
            <Typography variant="body2" color="text.secondary">
              x: {Math.round(detection.box.x)}, y: {Math.round(detection.box.y)}
              <br />
              width: {Math.round(detection.box.width)}, height: {Math.round(detection.box.height)}
            </Typography>
          </Box>

          {showLandmarks && detection.landmarks && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Facial Landmarks
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {detection.landmarks.positions.length} points detected
              </Typography>
            </Box>
          )}

          {showDescriptor && detection.descriptor && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Face Descriptor
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {detection.descriptor.length} features extracted
              </Typography>
            </Box>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
} 