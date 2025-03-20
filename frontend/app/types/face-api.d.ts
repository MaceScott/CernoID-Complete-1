declare global {
  interface Window {
    faceapi: {
      nets: {
        tinyFaceDetector: {
          load: (path: string) => Promise<void>;
        };
        faceLandmark68Net: {
          load: (path: string) => Promise<void>;
        };
        faceRecognitionNet: {
          load: (path: string) => Promise<void>;
        };
      };
      TinyFaceDetectorOptions: new (options?: { minConfidence?: number }) => any;
      detectSingleFace: (
        input: HTMLVideoElement | HTMLImageElement | HTMLCanvasElement,
        options: any
      ) => Promise<{
        score: number;
        box: {
          x: number;
          y: number;
          width: number;
          height: number;
        };
        withFaceLandmarks: () => Promise<{
          landmarks: {
            positions: Array<{ x: number; y: number }>;
          };
        }>;
        withFaceDescriptor: () => Promise<{
          descriptor: Float32Array;
        }>;
      } | null>;
      euclideanDistance: (
        descriptor1: Float32Array,
        descriptor2: Float32Array
      ) => number;
    };
  }
}

export {}; 