import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  Paper,
  Typography,
  Alert,
  CircularProgress
} from '@mui/material';
import { useAuth } from '../hooks/useAuth';

interface Permission {
  key: string;
  label: string;
  description: string;
}

interface PermissionManagerProps {
  userId: number;
  onUpdate?: () => void;
}

const AVAILABLE_PERMISSIONS: Permission[] = [
  {
    key: 'camera_access',
    label: 'Camera Access',
    description: 'Access device camera for video streaming'
  },
  {
    key: 'location_access',
    label: 'Location Access',
    description: 'Access device location for geolocation features'
  },
  {
    key: 'notification_access',
    label: 'Notification Access',
    description: 'Send push notifications to device'
  },
  {
    key: 'storage_access',
    label: 'Storage Access',
    description: 'Access device storage for saving data'
  }
];

export const PermissionManager: React.FC<PermissionManagerProps> = ({
  userId,
  onUpdate
}) => {
  const { user } = useAuth();
  const [permissions, setPermissions] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPermissions = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/mobile/permissions/${userId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch permissions');
        }
        const data = await response.json();
        setPermissions(data.permissions);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load permissions');
      } finally {
        setLoading(false);
      }
    };

    fetchPermissions();
  }, [userId]);

  const handlePermissionChange = (key: string) => {
    setPermissions((prev) => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const response = await fetch(`/api/mobile/permissions/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          permissions,
          adminId: user?.id
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update permissions');
      }

      setError(null);
      onUpdate?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save permissions');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Device Permissions
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mb: 3 }}>
        {AVAILABLE_PERMISSIONS.map((permission) => (
          <Box key={permission.key} sx={{ mb: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={permissions[permission.key] || false}
                  onChange={() => handlePermissionChange(permission.key)}
                  disabled={saving}
                />
              }
              label={
                <Box>
                  <Typography variant="subtitle1">{permission.label}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {permission.description}
                  </Typography>
                </Box>
              }
            />
          </Box>
        ))}
      </Box>

      <Button
        variant="contained"
        onClick={handleSave}
        disabled={saving}
        sx={{ minWidth: 120 }}
      >
        {saving ? <CircularProgress size={24} /> : 'Save Changes'}
      </Button>
    </Paper>
  );
}; 