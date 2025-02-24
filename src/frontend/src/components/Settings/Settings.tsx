import React, { useState, useEffect } from 'react';
import {
    Box,
    Paper,
    Typography,
    Grid,
    TextField,
    Switch,
    FormControlLabel,
    Button,
    Slider,
    Select,
    MenuItem,
    InputLabel,
    FormControl,
    Alert,
    CircularProgress,
    Divider,
    Accordion,
    AccordionSummary,
    AccordionDetails
} from '@mui/material';
import {
    ExpandMore as ExpandMoreIcon,
    Save as SaveIcon,
    Refresh as RefreshIcon
} from '@mui/icons-material';
import { useSettings } from '../../hooks/useSettings';

export const Settings: React.FC = () => {
    const { 
        settings, 
        loading, 
        error, 
        updateSettings, 
        resetSettings 
    } = useSettings();
    
    const [formData, setFormData] = useState({
        recognition: {
            min_confidence: 0.5,
            max_faces: 10,
            use_gpu: true,
            model_type: 'default'
        },
        security: {
            token_expiry: 30,
            max_attempts: 3,
            lockout_duration: 15,
            require_2fa: false
        },
        performance: {
            batch_size: 16,
            cache_enabled: true,
            cache_size: 1000,
            worker_threads: 4
        },
        monitoring: {
            metrics_enabled: true,
            log_level: 'info',
            retention_days: 30,
            alert_threshold: 0.9
        }
    });

    useEffect(() => {
        if (settings) {
            setFormData(settings);
        }
    }, [settings]);

    const handleSave = async () => {
        try {
            await updateSettings(formData);
        } catch (err) {
            console.error('Failed to update settings:', err);
        }
    };

    const handleReset = async () => {
        if (window.confirm('Are you sure you want to reset all settings?')) {
            try {
                await resetSettings();
            } catch (err) {
                console.error('Failed to reset settings:', err);
            }
        }
    };

    if (loading) {
        return (
            <Box sx={{ 
                display: 'flex', 
                justifyContent: 'center', 
                p: 3 
            }}>
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            <Box sx={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center',
                mb: 3 
            }}>
                <Typography variant="h4">Settings</Typography>
                <Box>
                    <Button
                        variant="outlined"
                        startIcon={<RefreshIcon />}
                        onClick={handleReset}
                        sx={{ mr: 2 }}
                    >
                        Reset
                    </Button>
                    <Button
                        variant="contained"
                        startIcon={<SaveIcon />}
                        onClick={handleSave}
                    >
                        Save Changes
                    </Button>
                </Box>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                </Alert>
            )}

            <Grid container spacing={3}>
                <Grid item xs={12}>
                    <Accordion defaultExpanded>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography variant="h6">Recognition Settings</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <Grid container spacing={2}>
                                <Grid item xs={12} md={6}>
                                    <Typography gutterBottom>
                                        Minimum Confidence Threshold
                                    </Typography>
                                    <Slider
                                        value={formData.recognition.min_confidence}
                                        onChange={(_, value) => setFormData({
                                            ...formData,
                                            recognition: {
                                                ...formData.recognition,
                                                min_confidence: value as number
                                            }
                                        })}
                                        min={0}
                                        max={1}
                                        step={0.05}
                                        valueLabelDisplay="auto"
                                        valueLabelFormat={(value) => 
                                            `${(value * 100).toFixed(0)}%`
                                        }
                                    />
                                </Grid>
                                <Grid item xs={12} md={6}>
                                    <TextField
                                        fullWidth
                                        label="Maximum Faces"
                                        type="number"
                                        value={formData.recognition.max_faces}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            recognition: {
                                                ...formData.recognition,
                                                max_faces: parseInt(e.target.value)
                                            }
                                        })}
                                    />
                                </Grid>
                                <Grid item xs={12} md={6}>
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={formData.recognition.use_gpu}
                                                onChange={(e) => setFormData({
                                                    ...formData,
                                                    recognition: {
                                                        ...formData.recognition,
                                                        use_gpu: e.target.checked
                                                    }
                                                })}
                                            />
                                        }
                                        label="Use GPU Acceleration"
                                    />
                                </Grid>
                                <Grid item xs={12} md={6}>
                                    <FormControl fullWidth>
                                        <InputLabel>Model Type</InputLabel>
                                        <Select
                                            value={formData.recognition.model_type}
                                            onChange={(e) => setFormData({
                                                ...formData,
                                                recognition: {
                                                    ...formData.recognition,
                                                    model_type: e.target.value
                                                }
                                            })}
                                            label="Model Type"
                                        >
                                            <MenuItem value="default">Default</MenuItem>
                                            <MenuItem value="fast">Fast</MenuItem>
                                            <MenuItem value="accurate">Accurate</MenuItem>
                                        </Select>
                                    </FormControl>
                                </Grid>
                            </Grid>
                        </AccordionDetails>
                    </Accordion>

                    {/* Similar accordions for Security, Performance, and Monitoring settings */}
                    <Accordion>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography variant="h6">Security Settings</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            {/* Security settings fields */}
                        </AccordionDetails>
                    </Accordion>

                    <Accordion>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography variant="h6">Performance Settings</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            {/* Performance settings fields */}
                        </AccordionDetails>
                    </Accordion>

                    <Accordion>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography variant="h6">Monitoring Settings</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            {/* Monitoring settings fields */}
                        </AccordionDetails>
                    </Accordion>
                </Grid>
            </Grid>
        </Box>
    );
}; 