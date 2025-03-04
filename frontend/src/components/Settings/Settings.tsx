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
    AccordionDetails,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    List,
    ListItem,
    ListItemText,
    ListItemSecondaryAction,
    Chip
} from '@mui/material';
import {
    ExpandMore as ExpandMoreIcon,
    Save as SaveIcon,
    Refresh as RefreshIcon,
    Add as AddIcon,
    Edit as EditIcon,
    Delete as DeleteIcon,
    AccessTime as AccessTimeIcon,
    Security as SecurityIcon,
    Camera as CameraIcon
} from '@mui/icons-material';
import { useSettings } from '@/hooks/useSettings';
import { useAccessControl } from '@/hooks/useAccessControl';
import { ZoneAccess, TimeSlot } from '@/types/access';
import { AppSettings } from '@/types';

export const Settings: React.FC = () => {
    const { 
        settings, 
        loading, 
        error, 
        updateSettings, 
        resetSettings 
    } = useSettings();

    const {
        zones,
        loading: zonesLoading,
        error: zonesError,
        checkAccess,
        requestAccess
    } = useAccessControl();
    
    const [formData, setFormData] = useState<AppSettings>({
        theme: 'light',
        language: 'en',
        notifications: {
            enabled: true,
            sound: true,
            desktop: true
        },
        security: {
            token_expiry: 30,
            max_attempts: 3,
            lockout_duration: 15,
            require_2fa: false,
            require_facial_recognition: true,
            require_password: true,
            allowed_admin_roles: ['admin', 'security']
        },
        display: {
            density: 'comfortable',
            fontSize: 14,
            showThumbnails: true
        },
        recognition: {
            min_confidence: 0.5,
            max_faces: 10,
            use_gpu: true,
            model_type: 'default'
        },
        system: {
            autoUpdate: true,
            logLevel: 'info',
            retentionDays: 30
        }
    });

    const [selectedZone, setSelectedZone] = useState<ZoneAccess | null>(null);
    const [zoneDialogOpen, setZoneDialogOpen] = useState(false);
    const [newTimeSlot, setNewTimeSlot] = useState<TimeSlot>({
        start: '09:00',
        end: '17:00',
        days: [1, 2, 3, 4, 5] // Monday to Friday
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

    const handleAddTimeSlot = () => {
        if (selectedZone) {
            const updatedZone = {
                ...selectedZone,
                allowedTimeSlots: [...selectedZone.allowedTimeSlots, newTimeSlot]
            };
            setSelectedZone(updatedZone);
            setNewTimeSlot({
                start: '09:00',
                end: '17:00',
                days: [1, 2, 3, 4, 5]
            });
        }
    };

    const handleRemoveTimeSlot = (index: number) => {
        if (selectedZone) {
            const updatedZone = {
                ...selectedZone,
                allowedTimeSlots: selectedZone.allowedTimeSlots.filter((_, i) => i !== index)
            };
            setSelectedZone(updatedZone);
        }
    };

    if (loading || zonesLoading) {
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
                    {/* Recognition Settings Accordion */}
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

                    {/* Security Settings Accordion */}
                    <Accordion>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography variant="h6">Security Settings</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <Grid container spacing={2}>
                                <Grid item xs={12} md={6}>
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={formData.security.require_facial_recognition}
                                                onChange={(e) => setFormData({
                                                    ...formData,
                                                    security: {
                                                        ...formData.security,
                                                        require_facial_recognition: e.target.checked
                                                    }
                                                })}
                                            />
                                        }
                                        label="Require Facial Recognition"
                                    />
                                </Grid>
                                <Grid item xs={12} md={6}>
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={formData.security.require_password}
                                                onChange={(e) => setFormData({
                                                    ...formData,
                                                    security: {
                                                        ...formData.security,
                                                        require_password: e.target.checked
                                                    }
                                                })}
                                            />
                                        }
                                        label="Require Password"
                                    />
                                </Grid>
                                <Grid item xs={12}>
                                    <FormControl fullWidth>
                                        <InputLabel>Allowed Admin Roles</InputLabel>
                                        <Select
                                            multiple
                                            value={formData.security.allowed_admin_roles}
                                            onChange={(e) => setFormData({
                                                ...formData,
                                                security: {
                                                    ...formData.security,
                                                    allowed_admin_roles: e.target.value as string[]
                                                }
                                            })}
                                            label="Allowed Admin Roles"
                                        >
                                            <MenuItem value="admin">Admin</MenuItem>
                                            <MenuItem value="security">Security</MenuItem>
                                            <MenuItem value="supervisor">Supervisor</MenuItem>
                                        </Select>
                                    </FormControl>
                                </Grid>
                            </Grid>
                        </AccordionDetails>
                    </Accordion>

                    {/* Camera Zones Accordion */}
                    <Accordion>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography variant="h6">Camera Zones</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <Box sx={{ mb: 2 }}>
                                <Button
                                    variant="contained"
                                    startIcon={<AddIcon />}
                                    onClick={() => {
                                        setSelectedZone({
                                            zoneId: '',
                                            name: '',
                                            description: '',
                                            accessLevel: 'free',
                                            allowedTimeSlots: [],
                                            restrictedTimeSlots: [],
                                            highSecurityTimeSlots: [],
                                            allowedRoles: []
                                        });
                                        setZoneDialogOpen(true);
                                    }}
                                >
                                    Add New Zone
                                </Button>
                            </Box>
                            <TableContainer component={Paper}>
                                <Table>
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>Name</TableCell>
                                            <TableCell>Description</TableCell>
                                            <TableCell>Access Level</TableCell>
                                            <TableCell>Allowed Roles</TableCell>
                                            <TableCell>Actions</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {zones.map((zone) => (
                                            <TableRow key={zone.zoneId}>
                                                <TableCell>{zone.name}</TableCell>
                                                <TableCell>{zone.description}</TableCell>
                                                <TableCell>
                                                    <Chip
                                                        icon={<AccessTimeIcon />}
                                                        label={zone.accessLevel}
                                                        color={
                                                            zone.accessLevel === 'free'
                                                                ? 'success'
                                                                : zone.accessLevel === 'restricted'
                                                                ? 'warning'
                                                                : 'error'
                                                        }
                                                        size="small"
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    {zone.allowedRoles.join(', ')}
                                                </TableCell>
                                                <TableCell>
                                                    <IconButton
                                                        onClick={() => {
                                                            setSelectedZone(zone);
                                                            setZoneDialogOpen(true);
                                                        }}
                                                    >
                                                        <EditIcon />
                                                    </IconButton>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </AccordionDetails>
                    </Accordion>

                    {/* Performance Settings Accordion */}
                    <Accordion>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography variant="h6">Performance Settings</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <Grid container spacing={2}>
                                <Grid item xs={12} md={6}>
                                    <TextField
                                        fullWidth
                                        label="Batch Size"
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
                            </Grid>
                        </AccordionDetails>
                    </Accordion>

                    {/* Monitoring Settings Accordion */}
                    <Accordion>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography variant="h6">Monitoring Settings</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <Grid container spacing={2}>
                                <Grid item xs={12} md={6}>
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={formData.system.autoUpdate}
                                                onChange={(e) => setFormData({
                                                    ...formData,
                                                    system: {
                                                        ...formData.system,
                                                        autoUpdate: e.target.checked
                                                    }
                                                })}
                                            />
                                        }
                                        label="Enable Auto Update"
                                    />
                                </Grid>
                                <Grid item xs={12} md={6}>
                                    <FormControl fullWidth>
                                        <InputLabel>Log Level</InputLabel>
                                        <Select
                                            value={formData.system.logLevel}
                                            onChange={(e) => setFormData({
                                                ...formData,
                                                system: {
                                                    ...formData.system,
                                                    logLevel: e.target.value as 'debug' | 'info' | 'warn' | 'error'
                                                }
                                            })}
                                            label="Log Level"
                                        >
                                            <MenuItem value="debug">Debug</MenuItem>
                                            <MenuItem value="info">Info</MenuItem>
                                            <MenuItem value="warn">Warning</MenuItem>
                                            <MenuItem value="error">Error</MenuItem>
                                        </Select>
                                    </FormControl>
                                </Grid>
                            </Grid>
                        </AccordionDetails>
                    </Accordion>
                </Grid>
            </Grid>

            {/* Zone Configuration Dialog */}
            <Dialog
                open={zoneDialogOpen}
                onClose={() => setZoneDialogOpen(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>
                    {selectedZone?.zoneId ? 'Edit Zone' : 'Add New Zone'}
                </DialogTitle>
                <DialogContent>
                    {selectedZone && (
                        <Grid container spacing={2} sx={{ mt: 1 }}>
                            <Grid item xs={12}>
                                <TextField
                                    fullWidth
                                    label="Zone Name"
                                    value={selectedZone.name}
                                    onChange={(e) => setSelectedZone({
                                        ...selectedZone,
                                        name: e.target.value
                                    })}
                                />
                            </Grid>
                            <Grid item xs={12}>
                                <TextField
                                    fullWidth
                                    label="Description"
                                    multiline
                                    rows={2}
                                    value={selectedZone.description}
                                    onChange={(e) => setSelectedZone({
                                        ...selectedZone,
                                        description: e.target.value
                                    })}
                                />
                            </Grid>
                            <Grid item xs={12} md={6}>
                                <FormControl fullWidth>
                                    <InputLabel>Access Level</InputLabel>
                                    <Select
                                        value={selectedZone.accessLevel}
                                        onChange={(e) => setSelectedZone({
                                            ...selectedZone,
                                            accessLevel: e.target.value as 'free' | 'restricted' | 'high-security'
                                        })}
                                        label="Access Level"
                                    >
                                        <MenuItem value="free">Free Access</MenuItem>
                                        <MenuItem value="restricted">Restricted</MenuItem>
                                        <MenuItem value="high-security">High Security</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                            <Grid item xs={12} md={6}>
                                <FormControl fullWidth>
                                    <InputLabel>Allowed Roles</InputLabel>
                                    <Select
                                        multiple
                                        value={selectedZone.allowedRoles}
                                        onChange={(e) => setSelectedZone({
                                            ...selectedZone,
                                            allowedRoles: e.target.value as string[]
                                        })}
                                        label="Allowed Roles"
                                    >
                                        <MenuItem value="admin">Admin</MenuItem>
                                        <MenuItem value="security">Security</MenuItem>
                                        <MenuItem value="user">User</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                            <Grid item xs={12}>
                                <Typography variant="subtitle1" gutterBottom>
                                    Allowed Time Slots
                                </Typography>
                                <List>
                                    {selectedZone.allowedTimeSlots.map((slot, index) => (
                                        <ListItem key={index}>
                                            <ListItemText
                                                primary={`${slot.start} - ${slot.end}`}
                                                secondary={`Days: ${slot.days.map(d => ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][d]).join(', ')}`}
                                            />
                                            <ListItemSecondaryAction>
                                                <IconButton
                                                    edge="end"
                                                    onClick={() => handleRemoveTimeSlot(index)}
                                                >
                                                    <DeleteIcon />
                                                </IconButton>
                                            </ListItemSecondaryAction>
                                        </ListItem>
                                    ))}
                                </List>
                                <Box sx={{ mt: 2 }}>
                                    <Grid container spacing={2}>
                                        <Grid item xs={12} md={4}>
                                            <TextField
                                                fullWidth
                                                label="Start Time"
                                                type="time"
                                                value={newTimeSlot.start}
                                                onChange={(e) => setNewTimeSlot({
                                                    ...newTimeSlot,
                                                    start: e.target.value
                                                })}
                                                InputLabelProps={{ shrink: true }}
                                            />
                                        </Grid>
                                        <Grid item xs={12} md={4}>
                                            <TextField
                                                fullWidth
                                                label="End Time"
                                                type="time"
                                                value={newTimeSlot.end}
                                                onChange={(e) => setNewTimeSlot({
                                                    ...newTimeSlot,
                                                    end: e.target.value
                                                })}
                                                InputLabelProps={{ shrink: true }}
                                            />
                                        </Grid>
                                        <Grid item xs={12} md={4}>
                                            <FormControl fullWidth>
                                                <InputLabel>Days</InputLabel>
                                                <Select
                                                    multiple
                                                    value={newTimeSlot.days}
                                                    onChange={(e) => setNewTimeSlot({
                                                        ...newTimeSlot,
                                                        days: e.target.value as number[]
                                                    })}
                                                    label="Days"
                                                >
                                                    <MenuItem value={0}>Sunday</MenuItem>
                                                    <MenuItem value={1}>Monday</MenuItem>
                                                    <MenuItem value={2}>Tuesday</MenuItem>
                                                    <MenuItem value={3}>Wednesday</MenuItem>
                                                    <MenuItem value={4}>Thursday</MenuItem>
                                                    <MenuItem value={5}>Friday</MenuItem>
                                                    <MenuItem value={6}>Saturday</MenuItem>
                                                </Select>
                                            </FormControl>
                                        </Grid>
                                    </Grid>
                                    <Button
                                        variant="outlined"
                                        startIcon={<AddIcon />}
                                        onClick={handleAddTimeSlot}
                                        sx={{ mt: 2 }}
                                    >
                                        Add Time Slot
                                    </Button>
                                </Box>
                            </Grid>
                        </Grid>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setZoneDialogOpen(false)}>
                        Cancel
                    </Button>
                    <Button
                        variant="contained"
                        onClick={() => {
                            // Save zone changes
                            setZoneDialogOpen(false);
                        }}
                    >
                        Save
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}; 