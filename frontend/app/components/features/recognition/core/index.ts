import { RecognitionOptions, FaceDetectionResult } from '@/types/recognition';

// Core components
export * from './RecognitionViewer';
export * from './RecognitionClient';
export * from './ResultsViewer';

export type { RecognitionOptions, FaceDetectionResult };

// Default configuration
export const DEFAULT_RECOGNITION_OPTIONS: RecognitionOptions = {
  confidenceThreshold: 0.7,
  detectLandmarks: true,
  extractDescriptor: true,
};

// Service functions
export async function detectFace(video: HTMLVideoElement, options: RecognitionOptions): Promise<FaceDetectionResult> {
  // Implementation will be added later
  throw new Error('Not implemented');
}

export function drawDetection(canvas: HTMLCanvasElement, detection: FaceDetectionResult): void {
  // Implementation will be added later
  throw new Error('Not implemented');
}

export async function captureFrame(video: HTMLVideoElement, detection: FaceDetectionResult): Promise<Blob> {
  // Implementation will be added later
  throw new Error('Not implemented');
} 