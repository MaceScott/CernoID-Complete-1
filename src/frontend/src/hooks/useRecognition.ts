import { useState } from 'react';
import { api } from '../services/api';

interface RecognitionResult {
  id: string;
  confidence: number;
  person: {
    id: string;
    name: string;
    role: string;
  };
  timestamp: string;
}

interface UseRecognitionReturn {
  processImage: (file: File) => Promise<RecognitionResult>;
  results: RecognitionResult[];
  loading: boolean;
  error: string | null;
}

export const useRecognition = (): UseRecognitionReturn => {
  const [results, setResults] = useState<RecognitionResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const processImage = async (file: File): Promise<RecognitionResult> => {
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await api.post('/recognition/process', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const result = response.data;
      setResults(prev => [...prev, result]);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to process image';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return {
    processImage,
    results,
    loading,
    error,
  };
}; 