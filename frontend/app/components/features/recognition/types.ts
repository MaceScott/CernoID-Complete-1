import type { RecognitionOptions } from '@/types/recognition';

// Default configuration
export const DEFAULT_RECOGNITION_OPTIONS: RecognitionOptions = {
  confidenceThreshold: 0.7,
  detectLandmarks: true,
  extractDescriptor: true,
}; 