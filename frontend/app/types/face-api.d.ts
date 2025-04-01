// import * as faceapi from 'face-api.js';

declare global {
  interface Window {
    faceapi: {
      nets: {
        tinyFaceDetector: any;
        faceLandmark68Net: any;
        faceRecognitionNet: any;
      };
      TinyFaceDetectorOptions: new (options?: { inputSize?: number; scoreThreshold?: number }) => any;
      detectSingleFace(
        input: HTMLVideoElement | HTMLImageElement | HTMLCanvasElement,
        options?: any
      ): Promise<FaceDetection | null>;
      euclideanDistance(descriptor1: Float32Array, descriptor2: Float32Array): number;
    };
  }
}

interface FaceDetection {
  box: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  score: number;
  landmarks?: {
    positions: Array<{
      x: number;
      y: number;
    }>;
  };
  descriptor?: Float32Array;
  withFaceLandmarks(): Promise<FaceDetectionWithLandmarks>;
  withFaceDescriptor(): Promise<FaceDetectionWithDescriptor>;
}

interface FaceDetectionWithLandmarks extends FaceDetection {
  landmarks: {
    positions: Array<{
      x: number;
      y: number;
    }>;
  };
}

interface FaceDetectionWithDescriptor extends FaceDetectionWithLandmarks {
  descriptor: Float32Array;
}

export {}; 