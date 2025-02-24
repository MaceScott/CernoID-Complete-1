import React, { useState, useCallback } from 'react';
import { 
    Box, 
    Button, 
    Typography, 
    CircularProgress,
    Paper,
    Alert
} from '@mui/material';
import { useDropzone } from 'react-dropzone';
import { theme } from '../../theme';
import { useRecognition } from '../../hooks/useRecognition';

export const ImageUpload: React.FC = () => {
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState('');
    const { processImage } = useRecognition();

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        if (acceptedFiles.length === 0) return;

        setProcessing(true);
        setError('');

        try {
            const file = acceptedFiles[0];
            const reader = new FileReader();

            reader.onload = async () => {
                const base64Image = reader.result as string;
                await processImage(base64Image);
            };

            reader.readAsDataURL(file);
        } catch (err) {
            setError('Failed to process image. Please try again.');
        } finally {
            setProcessing(false);
        }
    }, [processImage]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'image/*': ['.jpeg', '.jpg', '.png']
        },
        maxFiles: 1
    });

    return (
        <Box sx={{ p: 3 }}>
            <Paper
                elevation={3}
                sx={{
                    p: 4,
                    borderRadius: theme.shape.borderRadius
                }}
            >
                <Typography 
                    variant="h6" 
                    sx={{ mb: 2 }}
                >
                    Face Recognition
                </Typography>

                {error && (
                    <Alert 
                        severity="error" 
                        sx={{ mb: 2 }}
                    >
                        {error}
                    </Alert>
                )}

                <Box
                    {...getRootProps()}
                    sx={{
                        border: `2px dashed ${theme.palette.primary.main}`,
                        borderRadius: 1,
                        p: 3,
                        textAlign: 'center',
                        cursor: 'pointer',
                        bgcolor: isDragActive ? 
                            'action.hover' : 
                            'background.paper'
                    }}
                >
                    <input {...getInputProps()} />
                    {processing ? (
                        <CircularProgress />
                    ) : (
                        <Typography>
                            {isDragActive ?
                                'Drop the image here...' :
                                'Drag and drop an image here, or click to select'
                            }
                        </Typography>
                    )}
                </Box>
            </Paper>
        </Box>
    );
}; 