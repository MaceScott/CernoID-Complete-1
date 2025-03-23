import React from 'react';
import { FaceRegistration } from './FaceRegistration';
import { FaceVerification } from './FaceVerification';

export interface FaceRecognitionProps {
  mode: 'register' | 'verify';
  onSuccess?: () => void;
  onError: (error: Error) => void;
}

export const FaceRecognition: React.FC<FaceRecognitionProps> = ({ mode, onSuccess, onError }) => {
  return mode === 'register' ? (
    <FaceRegistration onSuccess={onSuccess} onError={onError} />
  ) : (
    <FaceVerification onSuccess={onSuccess} onError={onError} />
  );
};

export * from './FaceRegistration';
export * from './FaceVerification'; 