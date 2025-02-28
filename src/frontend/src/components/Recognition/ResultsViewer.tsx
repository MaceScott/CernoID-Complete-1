import React, { useRef, useEffect, useState } from 'react';
import {
    Box,
    Paper,
    Typography,
    Grid,
    Card,
    CardContent,
    Slider,
    Switch,
    FormControlLabel,
    IconButton,
    Tooltip,
    CircularProgress,
    Alert
} from '@mui/material';
import {
    ZoomIn,
    ZoomOut,
    Save as SaveIcon,
    FilterAlt as FilterIcon,
    Refresh as RefreshIcon
} from '@mui/icons-material';
import { theme } from '../../theme';

interface Face {
    bbox: number[];
    confidence: number;
    landmarks?: number[][];
    features?: number[];
}

interface ResultsViewerProps {
    imageUrl: string;
    faces: Face[];
    loading?: boolean;
    error?: string;
    onRefresh?: () => void;
}

export const ResultsViewer: React.FC<ResultsViewerProps> = ({
    imageUrl,
    faces,
    loading,
    error,
    onRefresh
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [zoom, setZoom] = useState(1);
    const [showLandmarks, setShowLandmarks] = useState(true);
    const [confidenceThreshold, setConfidenceThreshold] = useState(0.5);
    const [selectedFace, setSelectedFace] = useState<Face | null>(null);

    useEffect(() => {
        if (!imageUrl || !canvasRef.current) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const image = new Image();
        image.src = imageUrl;
        image.onload = () => {
            // Reset canvas and apply zoom
            canvas.width = image.width * zoom;
            canvas.height = image.height * zoom;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.scale(zoom, zoom);
            ctx.drawImage(image, 0, 0);

            // Draw faces that meet confidence threshold
            faces.forEach((face, index) => {
                if (face.confidence >= confidenceThreshold) {
                    const isSelected = selectedFace !== null && index === faces.indexOf(selectedFace);
                    drawFace(ctx, face, isSelected);
                }
            });
        };
    }, [imageUrl, faces, zoom, showLandmarks, confidenceThreshold, selectedFace]);

    const drawFace = (
        ctx: CanvasRenderingContext2D,
        face: Face,
        isSelected: boolean
    ) => {
        const [x1, y1, x2, y2] = face.bbox;

        // Draw bounding box
        ctx.strokeStyle = isSelected ? 
            theme.palette.secondary.main : 
            theme.palette.primary.main;
        ctx.lineWidth = 2;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

        // Draw confidence score
        ctx.fillStyle = theme.palette.background.paper;
        ctx.fillRect(x1, y1 - 20, 70, 20);
        ctx.fillStyle = theme.palette.text.primary;
        ctx.font = '12px Arial';
        ctx.fillText(
            `${(face.confidence * 100).toFixed(1)}%`,
            x1 + 5,
            y1 - 5
        );

        // Draw facial landmarks if enabled
        if (showLandmarks && face.landmarks) {
            ctx.fillStyle = theme.palette.secondary.main;
            face.landmarks.forEach(([x, y]) => {
                ctx.beginPath();
                ctx.arc(x, y, 2, 0, 2 * Math.PI);
                ctx.fill();
            });
        }
    };

    const handleSaveImage = () => {
        if (!canvasRef.current) return;
        
        const link = document.createElement('a');
        link.download = 'recognition-results.png';
        link.href = canvasRef.current.toDataURL();
        link.click();
    };

    return (
        <Box sx={{ p: 3 }}>
            <Grid container spacing={3}>
                <Grid item xs={12} md={8}>
                    <Paper 
                        sx={{ 
                            p: 2,
                            position: 'relative',
                            minHeight: 400
                        }}
                    >
                        {loading ? (
                            <Box sx={{
                                display: 'flex',
                                justifyContent: 'center',
                                alignItems: 'center',
                                height: '100%',
                                minHeight: 400
                            }}>
                                <CircularProgress />
                            </Box>
                        ) : error ? (
                            <Alert 
                                severity="error"
                                action={
                                    onRefresh && (
                                        <IconButton
                                            color="inherit"
                                            size="small"
                                            onClick={onRefresh}
                                        >
                                            <RefreshIcon />
                                        </IconButton>
                                    )
                                }
                            >
                                {error}
                            </Alert>
                        ) : (
                            <>
                                <Box sx={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    mb: 2
                                }}>
                                    <Typography variant="h6">
                                        Recognition Results
                                    </Typography>
                                    <Box>
                                        <Tooltip title="Zoom Out">
                                            <IconButton
                                                onClick={() => setZoom(z => Math.max(0.5, z - 0.1))}
                                            >
                                                <ZoomOut />
                                            </IconButton>
                                        </Tooltip>
                                        <Tooltip title="Zoom In">
                                            <IconButton
                                                onClick={() => setZoom(z => Math.min(2, z + 0.1))}
                                            >
                                                <ZoomIn />
                                            </IconButton>
                                        </Tooltip>
                                        <Tooltip title="Save Image">
                                            <IconButton onClick={handleSaveImage}>
                                                <SaveIcon />
                                            </IconButton>
                                        </Tooltip>
                                    </Box>
                                </Box>
                                <Box sx={{
                                    display: 'flex',
                                    justifyContent: 'center',
                                    overflow: 'auto'
                                }}>
                                    <canvas
                                        ref={canvasRef}
                                        style={{
                                            maxWidth: '100%',
                                            height: 'auto'
                                        }}
                                        onClick={(e) => {
                                            // Handle face selection on click
                                            const rect = canvasRef.current?.getBoundingClientRect();
                                            if (!rect) return;
                                            
                                            const x = (e.clientX - rect.left) / zoom;
                                            const y = (e.clientY - rect.top) / zoom;
                                            
                                            const clickedFace = faces.find(face => {
                                                const [x1, y1, x2, y2] = face.bbox;
                                                return x >= x1 && x <= x2 && y >= y1 && y <= y2;
                                            });
                                            
                                            setSelectedFace(clickedFace || null);
                                        }}
                                    />
                                </Box>
                            </>
                        )}
                    </Paper>
                </Grid>
                
                <Grid item xs={12} md={4}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Settings
                            </Typography>
                            
                            <Box sx={{ mb: 3 }}>
                                <Typography gutterBottom>
                                    Confidence Threshold
                                </Typography>
                                <Slider
                                    value={confidenceThreshold}
                                    onChange={(_, value) => 
                                        setConfidenceThreshold(value as number)
                                    }
                                    min={0}
                                    max={1}
                                    step={0.05}
                                    valueLabelDisplay="auto"
                                    valueLabelFormat={(value) => 
                                        `${(value * 100).toFixed(0)}%`
                                    }
                                />
                            </Box>
                            
                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={showLandmarks}
                                        onChange={(e) => 
                                            setShowLandmarks(e.target.checked)
                                        }
                                    />
                                }
                                label="Show Facial Landmarks"
                            />
                        </CardContent>
                    </Card>

                    {selectedFace && (
                        <Card sx={{ mt: 2 }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Face Details
                                </Typography>
                                <Typography>
                                    Confidence: {(selectedFace.confidence * 100).toFixed(1)}%
                                </Typography>
                                <Typography>
                                    Position: ({selectedFace.bbox[0]}, {selectedFace.bbox[1]})
                                </Typography>
                                <Typography>
                                    Size: {selectedFace.bbox[2] - selectedFace.bbox[0]} x{' '}
                                    {selectedFace.bbox[3] - selectedFace.bbox[1]} pixels
                                </Typography>
                            </CardContent>
                        </Card>
                    )}
                </Grid>
            </Grid>
        </Box>
    );
}; 