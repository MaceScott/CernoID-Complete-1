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
  const handleConfidenceChange = (_event: Event, value: number | number[]) => {
    onChange({
      ...options,
      minConfidence: Array.isArray(value) ? value[0] : value
    });
  };

  const handleToggleChange = (setting: keyof RecognitionOptions) => {
    return (_event: React.ChangeEvent<HTMLInputElement>) => {
      onChange({
        ...options,
        [setting]: !options[setting as keyof RecognitionOptions]
      });
    };
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
              Minimum Confidence ({(options.minConfidence * 100).toFixed(0)}%)
            </Typography>
            <Slider
              value={options.minConfidence}
              onChange={handleConfidenceChange}
              min={0.1}
              max={1}
              step={0.05}
              marks={[
                { value: 0.1, label: '10%' },
                { value: 0.5, label: '50%' },
                { value: 1, label: '100%' }
              ]}
            />
          </Box>

          <FormControlLabel
            control={
              <Switch
                checked={options.enableLandmarks}
                onChange={handleToggleChange('enableLandmarks')}
              />
            }
            label="Enable Facial Landmarks"
          />

          <FormControlLabel
            control={
              <Switch
                checked={options.enableDescriptors}
                onChange={handleToggleChange('enableDescriptors')}
              />
            }
            label="Enable Face Descriptors"
          />

          <FormControlLabel
            control={
              <Switch
                checked={options.useTinyModel}
                onChange={handleToggleChange('useTinyModel')}
              />
            }
            label="Use Lightweight Model"
          />
        </Stack>
      </CardContent>
    </Card>
  );
} 