'use client';

import { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Button,
  LinearProgress,
  Card,
  CardContent,
  CardHeader,
  Switch,
  FormControlLabel,
  TextField,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Storage as StorageIcon,
  Memory as MemoryIcon,
  Timer as TimerIcon,
  Update as UpdateIcon,
  Backup as BackupIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { useAuth } from '@/hooks/useAuth';
import { BaseFrame } from '@/desktop/BaseFrame';

interface SystemStatus {
  cpu: {
    usage: number;
    temperature: number;
  };
  memory: {
    total: number;
    used: number;
    free: number;
  };
  storage: {
    total: number;
    used: number;
    free: number;
    recordings: number;
    logs: number;
    backups: number;
    lastBackup: string;
  };
  uptime: number;
  lastUpdate: string;
}

interface MaintenanceLog {
  id: string;
  timestamp: string;
  type: string;
  details: string;
  status: 'success' | 'failed';
}

interface BackupConfig {
  schedule: string;
  retention: number;
  location: string;
}

export function SystemSettingsClient() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    cpu: { usage: 0, temperature: 0 },
    memory: { total: 0, used: 0, free: 0 },
    storage: { 
      total: 0, 
      used: 0, 
      free: 0,
      recordings: 0,
      logs: 0,
      backups: 0,
      lastBackup: new Date().toISOString()
    },
    uptime: 0,
    lastUpdate: new Date().toISOString()
  });
  const [maintenanceLogs, setMaintenanceLogs] = useState<MaintenanceLog[]>([]);
  const [backupConfig, setBackupConfig] = useState<BackupConfig>({
    schedule: '0 0 * * *',
    retention: 7,
    location: '/backups'
  });
  const [backupDialog, setBackupDialog] = useState(false);
  const [backupProgress, setBackupProgress] = useState(0);
  const [autoUpdate, setAutoUpdate] = useState(true);
  const [retentionDays, setRetentionDays] = useState('30');
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    fetchSystemStatus();
    fetchMaintenanceLogs();
    fetchBackupConfig();
    const interval = setInterval(fetchSystemStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/system/metrics`, {
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch system metrics');
      }
      
      const metrics = await response.json();
      const storageResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/system/storage`, {
        credentials: 'include',
      });
      
      if (!storageResponse.ok) {
        throw new Error('Failed to fetch storage metrics');
      }
      
      const storage = await storageResponse.json();
      
      setSystemStatus({
        cpu: { 
          usage: metrics.cpu, 
          temperature: 65 // Placeholder - implement actual temperature monitoring
        },
        memory: {
          total: metrics.memory.total,
          used: metrics.memory.used,
          free: metrics.memory.free
        },
        storage: {
          total: storage.total,
          used: storage.used,
          free: storage.available,
          recordings: storage.recordingsSize,
          logs: storage.logsSize,
          backups: storage.backupSize,
          lastBackup: storage.lastBackup
        },
        uptime: metrics.uptime,
        lastUpdate: metrics.lastUpdate
      });
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch system status');
      setLoading(false);
    }
  };

  const fetchMaintenanceLogs = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/system/logs`, {
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch maintenance logs');
      }
      
      const logs = await response.json();
      setMaintenanceLogs(logs);
    } catch (err) {
      console.error('Failed to fetch maintenance logs:', err);
    }
  };

  const fetchBackupConfig = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/system/backup-config`, {
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch backup config');
      }
      
      const config = await response.json();
      setBackupConfig(config);
    } catch (err) {
      console.error('Failed to fetch backup config:', err);
    }
  };

  const handleBackup = async () => {
    try {
      setBackupProgress(0);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/system/backup`, {
        method: 'POST',
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Backup failed');
      }
      
      // Simulate backup progress
      for (let i = 0; i <= 100; i += 10) {
        await new Promise(resolve => setTimeout(resolve, 500));
        setBackupProgress(i);
      }
      
      setBackupDialog(false);
      await fetchSystemStatus();
      await fetchMaintenanceLogs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Backup failed');
    }
  };

  const formatBytes = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  if (error) {
    return (
      <BaseFrame title="System Settings">
        <Container>
          <Alert severity="error" sx={{ mt: 4 }}>
            {error}
          </Alert>
        </Container>
      </BaseFrame>
    );
  }

  return (
    <BaseFrame title="System Settings">
      <Container maxWidth="xl">
        <Box sx={{ mt: 4 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h4" component="h1" gutterBottom>
              System Settings
            </Typography>
            <Button 
              variant="contained" 
              color="primary"
              startIcon={<BackupIcon />}
              onClick={() => setBackupDialog(true)}
            >
              Create Backup
            </Button>
          </Box>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Grid container spacing={3}>
              {/* System Status */}
              <Grid item xs={12} md={8}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    System Status
                  </Typography>
                  <Grid container spacing={3}>
                    <Grid item xs={12} sm={6}>
                      <Card>
                        <CardHeader
                          avatar={<MemoryIcon />}
                          title="CPU Usage"
                          subheader={`${systemStatus.cpu.usage}% | ${systemStatus.cpu.temperature}°C`}
                        />
                        <CardContent>
                          <LinearProgress
                            variant="determinate"
                            value={systemStatus.cpu.usage}
                            sx={{ height: 10, borderRadius: 5 }}
                          />
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Card>
                        <CardHeader
                          avatar={<StorageIcon />}
                          title="Memory"
                          subheader={`${formatBytes(systemStatus.memory.used)} / ${formatBytes(systemStatus.memory.total)}`}
                        />
                        <CardContent>
                          <LinearProgress
                            variant="determinate"
                            value={(systemStatus.memory.used / systemStatus.memory.total) * 100}
                            sx={{ height: 10, borderRadius: 5 }}
                          />
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12}>
                      <Card>
                        <CardHeader
                          avatar={<StorageIcon />}
                          title="Storage"
                          subheader={`${formatBytes(systemStatus.storage.used)} / ${formatBytes(systemStatus.storage.total)}`}
                        />
                        <CardContent>
                          <LinearProgress
                            variant="determinate"
                            value={(systemStatus.storage.used / systemStatus.storage.total) * 100}
                            sx={{ height: 10, borderRadius: 5 }}
                          />
                          <Grid container spacing={2} sx={{ mt: 2 }}>
                            <Grid item xs={4}>
                              <Typography variant="subtitle2" color="textSecondary">
                                Recordings
                              </Typography>
                              <Typography variant="body1">
                                {formatBytes(systemStatus.storage.recordings)}
                              </Typography>
                            </Grid>
                            <Grid item xs={4}>
                              <Typography variant="subtitle2" color="textSecondary">
                                Logs
                              </Typography>
                              <Typography variant="body1">
                                {formatBytes(systemStatus.storage.logs)}
                              </Typography>
                            </Grid>
                            <Grid item xs={4}>
                              <Typography variant="subtitle2" color="textSecondary">
                                Backups
                              </Typography>
                              <Typography variant="body1">
                                {formatBytes(systemStatus.storage.backups)}
                              </Typography>
                            </Grid>
                          </Grid>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>
                  <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>
                      <TimerIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                      Uptime: {formatUptime(systemStatus.uptime)}
                    </Typography>
                    <Typography>
                      Last Update: {new Date(systemStatus.lastUpdate).toLocaleString()}
                    </Typography>
                  </Box>
                </Paper>
              </Grid>

              {/* Settings */}
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Settings
                  </Typography>
                  <List>
                    <ListItem>
                      <ListItemText
                        primary="Automatic Updates"
                        secondary="Keep the system up to date automatically"
                      />
                      <ListItemSecondaryAction>
                        <Switch
                          edge="end"
                          checked={autoUpdate}
                          onChange={(e) => setAutoUpdate(e.target.checked)}
                        />
                      </ListItemSecondaryAction>
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Log Retention"
                        secondary="Number of days to keep system logs"
                      />
                      <ListItemSecondaryAction>
                        <TextField
                          type="number"
                          size="small"
                          value={retentionDays}
                          onChange={(e) => setRetentionDays(e.target.value)}
                          sx={{ width: 80 }}
                        />
                      </ListItemSecondaryAction>
                    </ListItem>
                  </List>
                  <Box sx={{ mt: 2 }}>
                    <Button
                      variant="contained"
                      color="primary"
                      disabled={updating}
                      onClick={() => fetchSystemStatus()}
                    >
                      Update Now
                    </Button>
                  </Box>
                </Paper>
              </Grid>

              {/* Maintenance Logs */}
              <Grid item xs={12}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Maintenance Logs
                  </Typography>
                  <List>
                    {maintenanceLogs.map(log => (
                      <ListItem key={log.id}>
                        <ListItemText
                          primary={log.type}
                          secondary={`${new Date(log.timestamp).toLocaleString()} - ${log.details}`}
                        />
                        <ListItemSecondaryAction>
                          <Typography
                            color={log.status === 'success' ? 'success.main' : 'error.main'}
                          >
                            {log.status}
                          </Typography>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                </Paper>
              </Grid>

              {/* Backup Configuration */}
              <Grid item xs={12}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Backup Configuration
                  </Typography>
                  <Grid container spacing={3}>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Backup Schedule (cron)"
                        value={backupConfig.schedule}
                        onChange={(e) => setBackupConfig({ ...backupConfig, schedule: e.target.value })}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        type="number"
                        label="Retention Days"
                        value={backupConfig.retention}
                        onChange={(e) => setBackupConfig({ ...backupConfig, retention: parseInt(e.target.value) })}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Backup Location"
                        value={backupConfig.location}
                        onChange={(e) => setBackupConfig({ ...backupConfig, location: e.target.value })}
                      />
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>
            </Grid>
          )}
        </Box>

        {/* Backup Dialog */}
        <Dialog open={backupDialog} onClose={() => setBackupDialog(false)}>
          <DialogTitle>Create System Backup</DialogTitle>
          <DialogContent>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              This will create a backup of all system data including:
              <ul>
                <li>User data and permissions</li>
                <li>Face recognition models</li>
                <li>System configurations</li>
                <li>Access logs</li>
              </ul>
            </Typography>
            {backupProgress > 0 && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress variant="determinate" value={backupProgress} />
                <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                  Progress: {backupProgress}%
                </Typography>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setBackupDialog(false)}>Cancel</Button>
            <Button 
              onClick={handleBackup} 
              variant="contained" 
              color="primary"
              disabled={backupProgress > 0}
            >
              Start Backup
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </BaseFrame>
  );
} 