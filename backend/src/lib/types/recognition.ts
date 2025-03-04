export interface Face {
    bbox: number[];
    confidence: number;
    landmarks?: number[][];
    features?: number[];
}

export interface RecognitionResult {
    id: string;
    timestamp: string;
    faces: Face[];
    processing_time: number;
    image_info: {
        width: number;
        height: number;
        format: string;
    };
} 