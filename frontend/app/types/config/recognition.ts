export interface RecognitionConfig {
  minConfidence: number;
  maxFaces: number;
  useGpu: boolean;
  modelType: string;
  enableLandmarks: boolean;
  enableDescriptors: boolean;
  processingTimeout: number;
  maxImageSize: number;
  supportedFormats: string[];
  batchSize: number;
  cacheSize: number;
  matcher: {
    algorithm: string;
    threshold: number;
    maxDistance: number;
  };
  registration: {
    maxAttempts: number;
    timeout: number;
    minQuality: number;
  };
}

export const DEFAULT_RECOGNITION_CONFIG: RecognitionConfig = {
  minConfidence: 0.85,
  maxFaces: 1,
  useGpu: false,
  modelType: 'default',
  enableLandmarks: true,
  enableDescriptors: true,
  processingTimeout: 5000,
  maxImageSize: 1920 * 1080,
  supportedFormats: ['jpeg', 'png', 'webp'],
  batchSize: 10,
  cacheSize: 1000,
  matcher: {
    algorithm: 'cosine',
    threshold: 0.85,
    maxDistance: 0.3,
  },
  registration: {
    maxAttempts: 3,
    timeout: 10000,
    minQuality: 0.8,
  },
}; 