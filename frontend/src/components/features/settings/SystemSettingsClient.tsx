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
  Divider
} from '@mui/material';
import {
  Storage as StorageIcon,
  Memory as MemoryIcon,
  Timer as TimerIcon,
  Update as UpdateIcon
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

export function SystemSettingsClient() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    cpu: { usage: 0, temperature: 0 },
    memory: { total: 0, used: 0, free: 0 },
    storage: { total: 0, used: 0, free: 0 },
    uptime: 0,
    lastUpdate: new Date().toISOString()
  });
  const [maintenanceLogs, setMaintenanceLogs] = useState<MaintenanceLog[]>([]);
  const [autoUpdate, setAutoUpdate] = useState(true);
  const [retentionDays, setRetentionDays] = useState('30');
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    fetchSystemStatus();
    fetchMaintenanceLogs();
    const interval = setInterval(fetchSystemStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchSystemStatus = async () => {
    try {
      // In a real app, this would be an API call
      setSystemStatus({
        cpu: { usage: 45, temperature: 65 },
        memory: {
          total: 16384,
          used: 8192,
          free: 8192
        },
        storage: {
          total: 1024000,
          used: 512000,
          free: 512000
        },
        uptime: 345600,
        lastUpdate: new Date().toISOString()
      });
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch system status');
      setLoading(false);
    }
  };

  const fetchMaintenanceLogs = async () => {
    try {
      // In a real app, this would be an API call
      setMaintenanceLogs([
        {
          id: '1',
          timestamp: new Date().toISOString(),
          type: 'System Update',
          details: 'Updated to version 1.2.3',
          status: 'success'
        },
        {
          id: '2',
          timestamp: new Date(Date.now() - 86400000).toISOString(),
          type: 'Backup',
          details: 'Daily backup completed',
          status: 'success'
        }
      ]);
    } catch (err) {
      console.error('Failed to fetch maintenance logs:', err);
    }
  };

  const handleSystemUpdate = async () => {
    try {
      setUpdating(true);
      // In a real app, this would be an API call
      await new Promise(resolve => setTimeout(resolve, 3000));
      await fetchSystemStatus();
      await fetchMaintenanceLogs();
    } catch (err) {
      setError('Failed to update system');
    } finally {
      setUpdating(false);
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
          <Typography variant="h4" component="h1" gutterBottom>
            System Settings
          </Typography>

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
                      startIcon={<UpdateIcon />}
                      fullWidth
                      onClick={handleSystemUpdate}
                      disabled={updating}
                    >
                      {updating ? 'Updating...' : 'Check for Updates'}
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
                          <Alert
                            severity={log.status === 'success' ? 'success' : 'error'}
                            sx={{ py: 0 }}
                          >
                            {log.status}
                          </Alert>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                </Paper>
              </Grid>
            </Grid>
          )}
        </Box>
      </Container>
    </BaseFrame>
  );
} 