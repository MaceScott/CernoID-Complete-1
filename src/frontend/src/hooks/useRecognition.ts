import { useState, useCallback } from 'react';
import { api } from '../services/api';
import { RecognitionResult } from '../types';

export const useRecognition = () => {
    const [results, setResults] = useState<RecognitionResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const processImage = useCallback(async (imageData: string) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await api.post('/recognition/process', {
                image: imageData
            });
            
            setResults(response.data);
            return response.data;
        } catch (err: any) {
            const errorMessage = err.response?.data?.message || 
                'Failed to process image';
            setError(errorMessage);
            throw new Error(errorMessage);
        } finally {
            setLoading(false);
        }
    }, []);

    const clearResults = useCallback(() => {
        setResults(null);
        setError(null);
    }, []);

    return {
        results,
        loading,
        error,
        processImage,
        clearResults
    };
}; 