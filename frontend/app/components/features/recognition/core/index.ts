// Core components
export * from './RecognitionViewer';
export * from './RecognitionClient';
export * from './ResultsViewer';

// Core types
export interface FaceDetectionResult {
  id: string;
  confidence: number;
  box: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  landmarks?: {
    positions: Array<{ x: number; y: number }>;
  };
  descriptor?: Float32Array;
}

export interface RecognitionOptions {
  minConfidence: number;
  enableLandmarks?: boolean;
  enableDescriptors?: boolean;
  maxResults?: number;
  useTinyModel?: boolean;
}

// Default configuration
export const DEFAULT_RECOGNITION_OPTIONS: RecognitionOptions = {
  minConfidence: 0.7,
  enableLandmarks: true,
  enableDescriptors: true,
  maxResults: 1,
  useTinyModel: true
}; 