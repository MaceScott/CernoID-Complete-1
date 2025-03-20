// Face detection types
export interface FaceDetectionResult {
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
  descriptor?: number[];
}

// Camera types
export interface CameraConfig {
  id: string;
  name: string;
  type: 'ip' | 'webcam' | 'file';
  url?: string;
  settings?: {
    resolution?: string;
    fps?: number;
    quality?: number;
  };
}

// Recognition result types
export interface RecognitionResult {
  id: string;
  success: boolean;
  face?: FaceDetectionResult;
  error?: string;
  timestamp: string;
  processingTime: number;
  imageInfo?: {
    width: number;
    height: number;
    format: string;
  };
} 