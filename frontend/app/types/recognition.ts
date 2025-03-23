export interface RecognitionOptions {
  confidenceThreshold: number;
  detectLandmarks: boolean;
  extractDescriptor: boolean;
}

export interface FaceDetectionResult {
  id: string;
  timestamp: number;
  boundingBox: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  confidence: number;
  landmarks?: Array<{
    x: number;
    y: number;
  }>;
  descriptor?: Float32Array;
}

export const DEFAULT_RECOGNITION_OPTIONS: RecognitionOptions = {
  confidenceThreshold: 0.7,
  detectLandmarks: true,
  extractDescriptor: true
}; 