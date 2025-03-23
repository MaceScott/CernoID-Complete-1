'use client';

import { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useAuth } from '@/hooks/useAuth';
import { BaseFrame } from '@/desktop/BaseFrame';
import { CameraConfig } from '@/types';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'viewer';
  status: 'active' | 'suspended';
}

interface Log {
  id: string;
  timestamp: string;
  type: 'login' | 'access' | 'system';
  user: string;
  action: string;
  details: string;
}

interface AdminClientProps {
  // ... props ...
}

export function AdminClient({ /* props */ }: AdminClientProps) {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState(0);
  const [users, setUsers] = useState<User[]>([]);
  const [cameras, setCameras] = useState<CameraConfig[]>([]);
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userDialog, setUserDialog] = useState<{
    open: boolean;
    user: Partial<User> | null;
  }>({ open: false, user: null });
  const [cameraDialog, setCameraDialog] = useState<{
    open: boolean;
    camera: Partial<CameraConfig> | null;
  }>({ open: false, camera: null });

  useEffect(() => {
    if (user?.role !== 'admin') {
      setError('Access denied. Admin privileges required.');
      return;
    }

    fetchData();
  }, [user]);

  const fetchData = async () => {
    try {
      setLoading(true);
      // In a real app, these would be API calls
      setUsers([
        { id: '1', name: 'Admin User', email: 'admin@example.com', role: 'admin', status: 'active' },
        { id: '2', name: 'Regular User', email: 'user@example.com', role: 'user', status: 'active' },
        { id: '3', name: 'Viewer', email: 'viewer@example.com', role: 'viewer', status: 'suspended' }
      ]);

      setCameras([
        {
          id: '1',
          name: 'Main Entrance',
          location: 'Front Door',
          type: 'facial',
          enabled: true,
          streamUrl: 'rtsp://example.com/camera1',
          status: 'active',
          url: 'rtsp://example.com/camera1',
          settings: { 
            resolution: '1080p', 
            fps: 30, 
            quality: 80,
            recording: true 
          },
          alerts: []
        },
        {
          id: '2',
          name: 'Parking Lot',
          location: 'Exterior',
          type: 'security',
          enabled: true,
          streamUrl: 'rtsp://example.com/camera2',
          status: 'active',
          url: 'rtsp://example.com/camera2',
          settings: { 
            resolution: '720p', 
            fps: 24, 
            quality: 80,
            recording: true 
          },
          alerts: []
        }
      ]);

      setLogs([
        {
          id: '1',
          timestamp: new Date().toISOString(),
          type: 'login',
          user: 'admin@example.com',
          action: 'Login successful',
          details: 'IP: 192.168.1.1'
        },
        {
          id: '2',
          timestamp: new Date().toISOString(),
          type: 'access',
          user: 'user@example.com',
          action: 'Access denied',
          details: 'Attempted to access admin page'
        }
      ]);
    } catch (err) {
      setError('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleUserSave = async (userData: Partial<User>) => {
    try {
      // In a real app, this would be an API call
      if (userData.id) {
        setUsers(prev => prev.map(u => u.id === userData.id ? { ...u, ...userData } : u));
      } else {
        setUsers(prev => [...prev, { ...userData, id: Date.now().toString() } as User]);
      }
      setUserDialog({ open: false, user: null });
    } catch (err) {
      setError('Failed to save user');
    }
  };

  const handleCameraSave = async (cameraData: Partial<CameraConfig>) => {
    try {
      // In a real app, this would be an API call
      if (cameraData.id) {
        setCameras(prev => prev.map(c => c.id === cameraData.id ? { ...c, ...cameraData } : c));
      } else {
        setCameras(prev => [...prev, { 
          ...cameraData, 
          id: Date.now().toString(),
          status: 'active',
          streamUrl: cameraData.url || '',
          settings: {
            resolution: '1080p',
            fps: 30,
            quality: 80,
            recording: false
          }
        } as CameraConfig]);
      }
      setCameraDialog({ open: false, camera: null });
    } catch (error) {
      console.error('Failed to save camera:', error);
    }
  };

  const handleUserDelete = async (userId: string) => {
    try {
      // In a real app, this would be an API call
      setUsers(prev => prev.filter(u => u.id !== userId));
    } catch (err) {
      setError('Failed to delete user');
    }
  };

  const handleCameraDelete = async (cameraId: string) => {
    try {
      // In a real app, this would be an API call
      setCameras(prev => prev.filter(c => c.id !== cameraId));
    } catch (err) {
      setError('Failed to delete camera');
    }
  };

  if (error) {
    return (
      <BaseFrame title="Administration">
        <Container>
          <Alert severity="error" sx={{ mt: 4 }}>
            {error}
          </Alert>
        </Container>
      </BaseFrame>
    );
  }

  return (
    <BaseFrame title="Administration">
      <Container maxWidth="xl">
        <Box sx={{ mt: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            System Administration
          </Typography>

          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs value={activeTab} onChange={(_, value) => setActiveTab(value)}>
              <Tab label="Users" />
              <Tab label="Cameras" />
              <Tab label="System Logs" />
            </Tabs>
          </Box>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              {/* Users Tab */}
              {activeTab === 0 && (
                <Box>
                  <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={() => setUserDialog({ open: true, user: {} })}
                    >
                      Add User
                    </Button>
                  </Box>
                  <Paper>
                    <List>
                      {users.map(user => (
                        <ListItem key={user.id}>
                          <ListItemText
                            primary={user.name}
                            secondary={`${user.email} - ${user.role} (${user.status})`}
                          />
                          <ListItemSecondaryAction>
                            <IconButton
                              edge="end"
                              onClick={() => setUserDialog({ open: true, user })}
                            >
                              <EditIcon />
                            </IconButton>
                            <IconButton
                              edge="end"
                              onClick={() => handleUserDelete(user.id)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </ListItemSecondaryAction>
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                </Box>
              )}

              {/* Cameras Tab */}
              {activeTab === 1 && (
                <Box>
                  <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={() => setCameraDialog({ open: true, camera: {} })}
                    >
                      Add Camera
                    </Button>
                  </Box>
                  <Paper>
                    <List>
                      {cameras.map(camera => (
                        <ListItem key={camera.id}>
                          <ListItemText
                            primary={camera.name}
                            secondary={`${camera.location} - ${camera.type} (${camera.enabled ? 'Enabled' : 'Disabled'})`}
                          />
                          <ListItemSecondaryAction>
                            <IconButton
                              edge="end"
                              onClick={() => setCameraDialog({ open: true, camera })}
                            >
                              <EditIcon />
                            </IconButton>
                            <IconButton
                              edge="end"
                              onClick={() => handleCameraDelete(camera.id)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </ListItemSecondaryAction>
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                </Box>
              )}

              {/* Logs Tab */}
              {activeTab === 2 && (
                <Box>
                  <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      variant="outlined"
                      startIcon={<RefreshIcon />}
                      onClick={fetchData}
                    >
                      Refresh Logs
                    </Button>
                  </Box>
                  <Paper>
                    <List>
                      {logs.map(log => (
                        <ListItem key={log.id}>
                          <ListItemText
                            primary={`${log.type.toUpperCase()}: ${log.action}`}
                            secondary={`${new Date(log.timestamp).toLocaleString()} - ${log.user} - ${log.details}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                </Box>
              )}
            </>
          )}
        </Box>

        {/* User Dialog */}
        <Dialog
          open={userDialog.open}
          onClose={() => setUserDialog({ open: false, user: null })}
        >
          <DialogTitle>
            {userDialog.user?.id ? 'Edit User' : 'Add User'}
          </DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 2 }}>
              <TextField
                fullWidth
                label="Name"
                value={userDialog.user?.name || ''}
                onChange={e => setUserDialog(prev => ({
                  ...prev,
                  user: { ...prev.user!, name: e.target.value }
                }))}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={userDialog.user?.email || ''}
                onChange={e => setUserDialog(prev => ({
                  ...prev,
                  user: { ...prev.user!, email: e.target.value }
                }))}
                sx={{ mb: 2 }}
              />
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Role</InputLabel>
                <Select
                  value={userDialog.user?.role || ''}
                  onChange={e => setUserDialog(prev => ({
                    ...prev,
                    user: { ...prev.user!, role: e.target.value as User['role'] }
                  }))}
                >
                  <MenuItem value="admin">Admin</MenuItem>
                  <MenuItem value="user">User</MenuItem>
                  <MenuItem value="viewer">Viewer</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={userDialog.user?.status || ''}
                  onChange={e => setUserDialog(prev => ({
                    ...prev,
                    user: { ...prev.user!, status: e.target.value as User['status'] }
                  }))}
                >
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="suspended">Suspended</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setUserDialog({ open: false, user: null })}>
              Cancel
            </Button>
            <Button
              variant="contained"
              onClick={() => handleUserSave(userDialog.user!)}
            >
              Save
            </Button>
          </DialogActions>
        </Dialog>

        {/* Camera Dialog */}
        <Dialog
          open={cameraDialog.open}
          onClose={() => setCameraDialog({ open: false, camera: null })}
        >
          <DialogTitle>
            {cameraDialog.camera?.id ? 'Edit Camera' : 'Add Camera'}
          </DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 2 }}>
              <TextField
                fullWidth
                label="Name"
                value={cameraDialog.camera?.name || ''}
                onChange={e => setCameraDialog(prev => ({
                  ...prev,
                  camera: { ...prev.camera!, name: e.target.value }
                }))}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Location"
                value={cameraDialog.camera?.location || ''}
                onChange={e => setCameraDialog(prev => ({
                  ...prev,
                  camera: { ...prev.camera!, location: e.target.value }
                }))}
                sx={{ mb: 2 }}
              />
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Type</InputLabel>
                <Select
                  value={cameraDialog.camera?.type || ''}
                  onChange={e => setCameraDialog(prev => ({
                    ...prev,
                    camera: { ...prev.camera!, type: e.target.value as CameraConfig['type'] }
                  }))}
                >
                  <MenuItem value="facial">Facial Recognition</MenuItem>
                  <MenuItem value="security">Security</MenuItem>
                  <MenuItem value="indoor">Indoor</MenuItem>
                  <MenuItem value="outdoor">Outdoor</MenuItem>
                </Select>
              </FormControl>
              <FormControlLabel
                control={
                  <Switch
                    checked={cameraDialog.camera?.enabled || false}
                    onChange={e => setCameraDialog(prev => ({
                      ...prev,
                      camera: { ...prev.camera!, enabled: e.target.checked }
                    }))}
                  />
                }
                label="Enabled"
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCameraDialog({ open: false, camera: null })}>
              Cancel
            </Button>
            <Button
              variant="contained"
              onClick={() => handleCameraSave(cameraDialog.camera!)}
            >
              Save
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </BaseFrame>
  );
} 