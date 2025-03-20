"use client"

import { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tooltip,
  Grid
} from '@mui/material';
import { FaceDetectionResult } from '../types';

interface FaceDetectionStatsProps {
  detection: FaceDetectionResult;
  onProcessingTime?: (time: number) => void;
}

interface DetectionStats {
  totalDetections: number;
  avgConfidence: number;
  successRate: number;
  avgProcessingTime: number;
  lastProcessingTime: number;
}

export function FaceDetectionStats({
  detection,
  onProcessingTime
}: FaceDetectionStatsProps) {
  const [stats, setStats] = useState<DetectionStats>({
    totalDetections: 0,
    avgConfidence: 0,
    successRate: 0,
    avgProcessingTime: 0,
    lastProcessingTime: 0
  });

  useEffect(() => {
    const startTime = performance.now();
    
    setStats(prevStats => {
      const processingTime = performance.now() - startTime;
      const newTotalDetections = prevStats.totalDetections + 1;
      
      const newStats = {
        totalDetections: newTotalDetections,
        avgConfidence: (prevStats.avgConfidence * prevStats.totalDetections + detection.confidence) / newTotalDetections,
        successRate: ((prevStats.successRate * prevStats.totalDetections + (detection.confidence > 0.7 ? 1 : 0)) / newTotalDetections) * 100,
        avgProcessingTime: (prevStats.avgProcessingTime * prevStats.totalDetections + processingTime) / newTotalDetections,
        lastProcessingTime: processingTime
      };

      if (onProcessingTime) {
        onProcessingTime(processingTime);
      }

      return newStats;
    });
  }, [detection, onProcessingTime]);

  const formatTime = (ms: number) => {
    return `${ms.toFixed(1)}ms`;
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Detection Statistics
        </Typography>

        <Grid container spacing={2}>
          <Grid item xs={6} sm={4}>
            <Typography variant="subtitle2" color="text.secondary">
              Total Detections
            </Typography>
            <Typography variant="h6">
              {stats.totalDetections}
            </Typography>
          </Grid>

          <Grid item xs={6} sm={4}>
            <Typography variant="subtitle2" color="text.secondary">
              Average Confidence
            </Typography>
            <Typography variant="h6">
              {(stats.avgConfidence * 100).toFixed(1)}%
            </Typography>
          </Grid>

          <Grid item xs={6} sm={4}>
            <Typography variant="subtitle2" color="text.secondary">
              Success Rate
            </Typography>
            <Typography variant="h6">
              {stats.successRate.toFixed(1)}%
            </Typography>
          </Grid>

          <Grid item xs={6} sm={4}>
            <Typography variant="subtitle2" color="text.secondary">
              Avg Processing Time
            </Typography>
            <Typography variant="h6">
              {formatTime(stats.avgProcessingTime)}
            </Typography>
          </Grid>

          <Grid item xs={6} sm={4}>
            <Tooltip title="Lower is better">
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Last Processing Time
                </Typography>
                <Typography variant="h6">
                  {formatTime(stats.lastProcessingTime)}
                </Typography>
              </Box>
            </Tooltip>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
} 