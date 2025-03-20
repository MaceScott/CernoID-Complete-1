'use client';

import React, { useState } from 'react';
import { Box, Typography, ToggleButtonGroup, ToggleButton } from '@mui/material';
import MultiCameraGrid from '@/components/features/cameras/MultiCameraGrid';
import { AuthGuard } from '@/components/Auth';

export default function MultiCameraPage() {
  const [layout, setLayout] = useState<'2x2' | '3x3' | '4x4'>('2x2');
  const [quality, setQuality] = useState<'low' | 'medium' | 'high'>('medium');

  const handleLayoutChange = (event: React.MouseEvent<HTMLElement>, newLayout: '2x2' | '3x3' | '4x4' | null) => {
    if (newLayout !== null) {
      setLayout(newLayout);
    }
  };

  const handleQualityChange = (event: React.MouseEvent<HTMLElement>, newQuality: 'low' | 'medium' | 'high' | null) => {
    if (newQuality !== null) {
      setQuality(newQuality);
    }
  };

  return (
    <AuthGuard>
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Multi-Camera View
        </Typography>
        <Box sx={{ mb: 3 }}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              Layout
            </Typography>
            <ToggleButtonGroup
              value={layout}
              exclusive
              onChange={handleLayoutChange}
              aria-label="camera layout"
            >
              <ToggleButton value="2x2" aria-label="2x2 grid">
                2x2
              </ToggleButton>
              <ToggleButton value="3x3" aria-label="3x3 grid">
                3x3
              </ToggleButton>
              <ToggleButton value="4x4" aria-label="4x4 grid">
                4x4
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Quality
            </Typography>
            <ToggleButtonGroup
              value={quality}
              exclusive
              onChange={handleQualityChange}
              aria-label="stream quality"
            >
              <ToggleButton value="low" aria-label="low quality">
                Low
              </ToggleButton>
              <ToggleButton value="medium" aria-label="medium quality">
                Medium
              </ToggleButton>
              <ToggleButton value="high" aria-label="high quality">
                High
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>
        </Box>
        <MultiCameraGrid layout={layout} quality={quality} />
      </Box>
    </AuthGuard>
  );
} 