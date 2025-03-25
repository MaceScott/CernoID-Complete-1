"use client"

import {
  Box,
  Card,
  CardContent,
  Typography,
  Slider,
  Switch,
  FormControlLabel,
  Stack
} from '@mui/material';
import { RecognitionOptions } from '@/types/recognition';

interface FaceDetectionSettingsProps {
  options: RecognitionOptions;
  onChange: (options: RecognitionOptions) => void;
}

export function FaceDetectionSettings({
  options,
  onChange
}: FaceDetectionSettingsProps) {
  const handleConfidenceChange = (_: Event, value: number | number[]) => {
    onChange({
      ...options,
      confidenceThreshold: Array.isArray(value) ? value[0] : value
    });
  };

  const handleToggleChange = (key: keyof RecognitionOptions) => (_: React.ChangeEvent<HTMLInputElement>) => {
    onChange({
      ...options,
      [key]: !options[key]
    });
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Detection Settings
        </Typography>

        <Stack spacing={3}>
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Confidence Threshold ({(options.confidenceThreshold * 100).toFixed(0)}%)
            </Typography>
            <Slider
              value={options.confidenceThreshold}
              onChange={handleConfidenceChange}
              min={0.1}
              max={1.0}
              step={0.05}
              marks={[
                { value: 0.1, label: '10%' },
                { value: 0.5, label: '50%' },
                { value: 1.0, label: '100%' }
              ]}
            />
          </Box>

          <FormControlLabel
            control={
              <Switch
                checked={options.detectLandmarks}
                onChange={handleToggleChange('detectLandmarks')}
              />
            }
            label="Detect Facial Landmarks"
          />

          <FormControlLabel
            control={
              <Switch
                checked={options.extractDescriptor}
                onChange={handleToggleChange('extractDescriptor')}
              />
            }
            label="Extract Face Descriptor"
          />
        </Stack>
      </CardContent>
    </Card>
  );
} 