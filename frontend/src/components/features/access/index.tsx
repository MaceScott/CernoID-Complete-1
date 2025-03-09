import React, { useState } from 'react';
import {
    Box,
    Paper,
    Typography,
    Grid,
    Card,
    CardContent,
    CardActions,
    Button,
    Chip,
    Alert,
    CircularProgress,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    List,
    ListItem,
    ListItemText,
    ListItemSecondaryAction,
    IconButton,
    Divider
} from '@mui/material';
import {
    AccessTime as AccessTimeIcon,
    Warning as WarningIcon,
    Security as SecurityIcon,
    CheckCircle as CheckCircleIcon,
    Cancel as CancelIcon,
    Close as CloseIcon
} from '@mui/icons-material';
import { useAccessControl } from '@/hooks/useAccessControl';
import { AccessAlert, ZoneAccess } from '@/types/access';

export const AccessControl: React.FC = () => {
    const {
        zones,
        alerts,
        loading,
        error,
        checkAccess,
        requestAccess,
        resolveAlert,
        dismissAlert
    } = useAccessControl();

    const [selectedZone, setSelectedZone] = useState<ZoneAccess | null>(null);
    const [selectedAlert, setSelectedAlert] = useState<AccessAlert | null>(null);

    const handleZoneClick = async (zone: ZoneAccess) => {
        setSelectedZone(zone);
        const hasAccess = await checkAccess(zone.zoneId);
        if (hasAccess) {
            await requestAccess(zone.zoneId);
        }
    };

    const handleAlertClick = (alert: AccessAlert) => {
        setSelectedAlert(alert);
    };

    const getAlertSeverity = (type: AccessAlert['type']) => {
        switch (type) {
            case 'high-security':
                return 'error';
            case 'restricted':
                return 'warning';
            case 'unauthorized':
                return 'info';
            default:
                return 'info';
        }
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="error">{error}</Alert>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            <Grid container spacing={3}>
                {/* Zones Section */}
                <Grid item xs={12} md={8}>
                    <Typography variant="h5" gutterBottom>
                        Access Zones
                    </Typography>
                    <Grid container spacing={2}>
                        {zones.map((zone) => (
                            <Grid item xs={12} sm={6} key={zone.zoneId}>
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6">
                                            {zone.name}
                                        </Typography>
                                        <Typography color="textSecondary" gutterBottom>
                                            {zone.description}
                                        </Typography>
                                        <Box sx={{ mt: 1 }}>
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
                                                sx={{ mr: 1 }}
                                            />
                                            <Chip
                                                label={`${zone.currentOccupancy || 0}/${zone.maxOccupancy || '∞'}`}
                                                size="small"
                                            />
                                        </Box>
                                    </CardContent>
                                    <CardActions>
                                        <Button
                                            size="small"
                                            onClick={() => handleZoneClick(zone)}
                                        >
                                            Request Access
                                        </Button>
                                    </CardActions>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                </Grid>

                {/* Alerts Section */}
                <Grid item xs={12} md={4}>
                    <Typography variant="h5" gutterBottom>
                        Security Alerts
                    </Typography>
                    <List>
                        {alerts.map((alert) => (
                            <React.Fragment key={alert.id}>
                                <ListItem
                                    button
                                    onClick={() => handleAlertClick(alert)}
                                >
                                    <ListItemText
                                        primary={
                                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                                {alert.type === 'high-security' && (
                                                    <SecurityIcon color="error" sx={{ mr: 1 }} />
                                                )}
                                                {alert.type === 'restricted' && (
                                                    <WarningIcon color="warning" sx={{ mr: 1 }} />
                                                )}
                                                {alert.type === 'unauthorized' && (
                                                    <CancelIcon color="info" sx={{ mr: 1 }} />
                                                )}
                                                {alert.userName}
                                            </Box>
                                        }
                                        secondary={`${alert.type} - ${new Date(alert.timestamp).toLocaleString()}`}
                                    />
                                    <ListItemSecondaryAction>
                                        <IconButton
                                            edge="end"
                                            onClick={() => dismissAlert(alert.id)}
                                        >
                                            <CloseIcon />
                                        </IconButton>
                                    </ListItemSecondaryAction>
                                </ListItem>
                                <Divider />
                            </React.Fragment>
                        ))}
                    </List>
                </Grid>
            </Grid>

            {/* Zone Details Dialog */}
            <Dialog
                open={!!selectedZone}
                onClose={() => setSelectedZone(null)}
                maxWidth="sm"
                fullWidth
            >
                {selectedZone && (
                    <>
                        <DialogTitle>
                            {selectedZone.name} Access Details
                        </DialogTitle>
                        <DialogContent>
                            <Typography variant="body1" paragraph>
                                {selectedZone.description}
                            </Typography>
                            <Typography variant="subtitle1" gutterBottom>
                                Access Schedule:
                            </Typography>
                            <List>
                                {selectedZone.allowedTimeSlots.map((slot, index) => (
                                    <ListItem key={index}>
                                        <ListItemText
                                            primary={`${slot.start} - ${slot.end}`}
                                            secondary={`Days: ${slot.days.map(d => ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][d]).join(', ')}`}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={() => setSelectedZone(null)}>
                                Close
                            </Button>
                        </DialogActions>
                    </>
                )}
            </Dialog>

            {/* Alert Details Dialog */}
            <Dialog
                open={!!selectedAlert}
                onClose={() => setSelectedAlert(null)}
                maxWidth="sm"
                fullWidth
            >
                {selectedAlert && (
                    <>
                        <DialogTitle>
                            Alert Details
                        </DialogTitle>
                        <DialogContent>
                            <Alert
                                severity={getAlertSeverity(selectedAlert.type)}
                                sx={{ mb: 2 }}
                            >
                                {selectedAlert.type === 'high-security'
                                    ? 'High Security Alert'
                                    : selectedAlert.type === 'restricted'
                                    ? 'Restricted Access Attempt'
                                    : 'Unauthorized Access Attempt'}
                            </Alert>
                            <List>
                                <ListItem>
                                    <ListItemText
                                        primary="User"
                                        secondary={selectedAlert.userName}
                                    />
                                </ListItem>
                                <ListItem>
                                    <ListItemText
                                        primary="Time"
                                        secondary={new Date(selectedAlert.timestamp).toLocaleString()}
                                    />
                                </ListItem>
                                <ListItem>
                                    <ListItemText
                                        primary="Details"
                                        secondary={JSON.stringify(selectedAlert.details, null, 2)}
                                    />
                                </ListItem>
                            </List>
                        </DialogContent>
                        <DialogActions>
                            <Button
                                onClick={() => resolveAlert(selectedAlert.id)}
                                color="primary"
                            >
                                Resolve
                            </Button>
                            <Button onClick={() => setSelectedAlert(null)}>
                                Close
                            </Button>
                        </DialogActions>
                    </>
                )}
            </Dialog>
        </Box>
    );
}; 