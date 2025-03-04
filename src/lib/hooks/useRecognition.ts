import { useState } from 'react';
import { apiClient } from '../api/api-client';
import { RecognitionResult } from '../types/recognition';

interface UseRecognitionReturn {
    processImage: (imageData: string) => Promise<RecognitionResult>;
    loading: boolean;
    error: string | null;
}

export function useRecognition(): UseRecognitionReturn {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const processImage = async (imageData: string): Promise<RecognitionResult> => {
        try {
            setLoading(true);
            setError(null);
            const result = await apiClient.recognition.processImage(imageData);
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
        loading,
        error
    };
} 