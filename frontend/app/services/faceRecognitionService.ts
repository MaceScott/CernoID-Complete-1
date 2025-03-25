import * as faceapi from 'face-api.js';
import { FaceDetectionResult, RecognitionOptions } from '@/types/recognition';

class FaceRecognitionService {
  private isInitialized = false;

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    await Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri('/models'),
      faceapi.nets.faceLandmark68Net.loadFromUri('/models'),
      faceapi.nets.faceRecognitionNet.loadFromUri('/models')
    ]);

    this.isInitialized = true;
  }

  async detectFace(
    video: HTMLVideoElement,
    options: RecognitionOptions
  ): Promise<FaceDetectionResult | null> {
    const detection = await faceapi
      .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
      .withFaceLandmarks()
      .withFaceDescriptor();

    if (!detection || detection.detection.score < options.confidenceThreshold) {
      return null;
    }

    const result: FaceDetectionResult = {
      id: Math.random().toString(36).substring(7),
      timestamp: Date.now(),
      boundingBox: {
        x: detection.detection.box.x,
        y: detection.detection.box.y,
        width: detection.detection.box.width,
        height: detection.detection.box.height
      },
      confidence: detection.detection.score,
      landmarks: options.detectLandmarks ? detection.landmarks.positions : undefined,
      descriptor: options.extractDescriptor ? detection.descriptor : undefined
    };

    return result;
  }

  async captureFrame(
    video: HTMLVideoElement,
    detection: FaceDetectionResult
  ): Promise<Blob> {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');

    if (!ctx) {
      throw new Error('Could not get canvas context');
    }

    ctx.drawImage(video, 0, 0);

    // Crop to face
    const { x, y, width, height } = detection.boundingBox;
    const padding = 50;
    const cropCanvas = document.createElement('canvas');
    cropCanvas.width = width + padding * 2;
    cropCanvas.height = height + padding * 2;
    const cropCtx = cropCanvas.getContext('2d');

    if (!cropCtx) {
      throw new Error('Could not get crop canvas context');
    }

    cropCtx.drawImage(
      canvas,
      x - padding,
      y - padding,
      width + padding * 2,
      height + padding * 2,
      0,
      0,
      width + padding * 2,
      height + padding * 2
    );

    return new Promise((resolve, reject) => {
      cropCanvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error('Could not create blob from canvas'));
          }
        },
        'image/jpeg',
        0.95
      );
    });
  }

  drawDetection(canvas: HTMLCanvasElement, detection: FaceDetectionResult): void {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 2;

    const { x, y, width, height } = detection.boundingBox;
    ctx.strokeRect(x, y, width, height);

    if (detection.landmarks) {
      ctx.fillStyle = '#00ff00';
      detection.landmarks.forEach((point) => {
        ctx.beginPath();
        ctx.arc(point.x, point.y, 2, 0, 2 * Math.PI);
        ctx.fill();
      });
    }
  }
}

export const faceRecognitionService = new FaceRecognitionService(); 