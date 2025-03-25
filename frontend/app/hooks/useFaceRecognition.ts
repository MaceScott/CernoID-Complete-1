import { useCallback, useEffect, useRef, useState } from 'react';
import { faceRecognitionService } from '@/services/faceRecognitionService';
import { FaceDetectionResult, RecognitionOptions } from '@/types/recognition';

interface UseFaceRecognitionOptions {
  onDetection?: (detection: FaceDetectionResult) => void;
  onCapture?: (faceData: FormData) => void;
  onError?: (error: Error) => void;
  recognitionOptions?: Partial<RecognitionOptions>;
  autoStart?: boolean;
  captureThreshold?: number;
}

interface UseFaceRecognitionReturn {
  videoRef: React.RefObject<HTMLVideoElement>;
  canvasRef: React.RefObject<HTMLCanvasElement>;
  isInitialized: boolean;
  isLoading: boolean;
  error: string | null;
  startRecognition: () => Promise<void>;
  stopRecognition: () => void;
}

export function useFaceRecognition({
  onDetection,
  onCapture,
  onError,
  recognitionOptions,
  autoStart = true,
  captureThreshold = 0.8
}: UseFaceRecognitionOptions = {}): UseFaceRecognitionReturn {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleError = useCallback((err: Error) => {
    setError(err.message);
    onError?.(err);
  }, [onError]);

  const startVideo = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user' }
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      handleError(new Error('Failed to access camera'));
    }
  }, [handleError]);

  const stopVideo = useCallback(() => {
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
  }, []);

  const startRecognition = useCallback(async () => {
    if (!isInitialized) {
      try {
        await faceRecognitionService.initialize();
        setIsInitialized(true);
      } catch (err) {
        handleError(new Error('Failed to initialize face recognition'));
        return;
      }
    }

    await startVideo();
    setIsLoading(false);
  }, [isInitialized, startVideo, handleError]);

  const stopRecognition = useCallback(() => {
    stopVideo();
    setIsLoading(true);
  }, [stopVideo]);

  useEffect(() => {
    if (autoStart) {
      startRecognition();
    }

    return () => {
      stopRecognition();
    };
  }, [autoStart, startRecognition, stopRecognition]);

  const handleVideoPlay = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const detectFace = async () => {
      try {
        const detection = await faceRecognitionService.detectFace(videoRef.current!, {
          confidenceThreshold: 0.7,
          detectLandmarks: true,
          extractDescriptor: true,
          ...recognitionOptions
        });

        if (detection && canvasRef.current) {
          faceRecognitionService.drawDetection(canvasRef.current, detection);
          onDetection?.(detection);

          if (detection.confidence > captureThreshold && onCapture) {
            const faceBlob = await faceRecognitionService.captureFrame(
              videoRef.current!,
              detection
            );

            const formData = new FormData();
            formData.append('face', faceBlob as Blob, 'face.jpg');
            onCapture(formData);
            stopRecognition();
          }
        }

        if (videoRef.current?.readyState === 4) {
          requestAnimationFrame(detectFace);
        }
      } catch (err) {
        handleError(new Error('Face detection failed'));
      }
    };

    detectFace();
  }, [onDetection, onCapture, captureThreshold, recognitionOptions, stopRecognition, handleError]);

  useEffect(() => {
    const video = videoRef.current;
    if (video) {
      video.addEventListener('play', handleVideoPlay);
      return () => {
        video.removeEventListener('play', handleVideoPlay);
      };
    }
  }, [handleVideoPlay]);

  return {
    videoRef,
    canvasRef,
    isInitialized,
    isLoading,
    error,
    startRecognition,
    stopRecognition
  };
} 