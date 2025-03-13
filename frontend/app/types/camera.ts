export interface Camera {
  id: string;
  name: string;
  streamUrl: string;
  type: 'facial' | 'security';
  location: string;
  status: 'online' | 'offline';
  lastSeen?: string;
  resolution?: {
    width: number;
    height: number;
  };
  capabilities: {
    faceDetection: boolean;
    motionDetection: boolean;
    nightVision: boolean;
    twoWayAudio: boolean;
  };
} 