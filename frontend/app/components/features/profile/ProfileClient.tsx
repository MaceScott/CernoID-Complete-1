'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Avatar,
  Button,
  TextField,
  Grid,
  Divider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  IconButton,
} from '@mui/material';
import { useAuth } from '@/hooks/useAuth';
import { z } from 'zod';
import { withErrorBoundary } from '@/components/shared/feedback';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Help as HelpIcon,
} from '@mui/icons-material';
import { ScreenReaderOnly } from '../../ui/ScreenReaderOnly';

const profileSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  currentPassword: z.string().min(1, 'Current password is required'),
  newPassword: z.string().min(8, 'Password must be at least 8 characters').optional(),
  confirmPassword: z.string().optional(),
});

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  title,
  message,
  onConfirm,
  onCancel,
}) => (
  <Dialog open={open} onClose={onCancel}>
    <DialogTitle>{title}</DialogTitle>
    <DialogContent>
      <Typography>{message}</Typography>
    </DialogContent>
    <DialogActions>
      <Button onClick={onCancel}>Cancel</Button>
      <Button onClick={onConfirm} color="error" variant="contained">
        Confirm
      </Button>
    </DialogActions>
  </Dialog>
);

export function ProfileClient() {
  const { user } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
  }>({
    open: false,
    title: '',
    message: '',
    onConfirm: () => {},
  });
  const formRef = useRef<HTMLFormElement>(null);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isEditing) {
        handleCancel();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 's' && isEditing) {
        e.preventDefault();
        handleSubmit(e as unknown as React.FormEvent);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isEditing]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError(null);
  };

  const showConfirmDialog = (title: string, message: string, onConfirm: () => void) => {
    setConfirmDialog({
      open: true,
      title,
      message,
      onConfirm,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Show confirmation dialog for profile updates
    showConfirmDialog(
      'Update Profile',
      'Are you sure you want to update your profile information?',
      async () => {
        setError(null);
        setSuccess(null);

        try {
          // Validate form data
          const validatedData = profileSchema.parse(formData);

          // Check if passwords match when changing password
          if (validatedData.newPassword && validatedData.newPassword !== formData.confirmPassword) {
            throw new Error('New passwords do not match');
          }

          // Call API to update profile
          const response = await fetch('/api/profile/update', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(validatedData),
          });

          if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || 'Failed to update profile');
          }

          setSuccess('Profile updated successfully');
          setIsEditing(false);
          setConfirmDialog(prev => ({ ...prev, open: false }));
        } catch (err) {
          if (err instanceof z.ZodError) {
            setError(err.errors[0].message);
          } else if (err instanceof Error) {
            setError(err.message);
          } else {
            setError('An unexpected error occurred');
          }
          setConfirmDialog(prev => ({ ...prev, open: false }));
        }
      }
    );
  };

  const handleCancel = () => {
    setIsEditing(false);
    setError(null);
    setFormData({
      name: user?.name || '',
      email: user?.email || '',
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    });
  };

  return (
    <Box 
      sx={{ maxWidth: 800, mx: 'auto', p: 3 }}
      role="main"
      aria-label="Profile Settings"
    >
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
            <Avatar
              sx={{ width: 100, height: 100, mr: 3 }}
              src={user?.avatar}
              alt={`${user?.name}'s profile picture`}
            />
            <Box>
              <Typography variant="h4" gutterBottom component="h1">
                Profile Settings
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Manage your account settings and security preferences
              </Typography>
            </Box>
          </Box>

          {error && (
            <Alert 
              severity="error" 
              sx={{ mb: 2 }}
              role="alert"
              aria-live="assertive"
            >
              {error}
            </Alert>
          )}

          {success && (
            <Alert 
              severity="success" 
              sx={{ mb: 2 }}
              role="alert"
              aria-live="polite"
            >
              {success}
            </Alert>
          )}

          <form 
            onSubmit={handleSubmit}
            ref={formRef}
            aria-label="Profile edit form"
          >
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  disabled={!isEditing}
                  inputProps={{
                    'aria-label': 'Name',
                    'aria-required': 'true',
                  }}
                  onFocus={() => setFocusedField('name')}
                  onBlur={() => setFocusedField(null)}
                  helperText={focusedField === 'name' ? 'Enter your full name' : ' '}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  disabled={!isEditing}
                  inputProps={{
                    'aria-label': 'Email address',
                    'aria-required': 'true',
                  }}
                  onFocus={() => setFocusedField('email')}
                  onBlur={() => setFocusedField(null)}
                  helperText={focusedField === 'email' ? 'Enter your email address' : ' '}
                />
              </Grid>

              {isEditing && (
                <>
                  <Grid item xs={12}>
                    <Divider sx={{ my: 2 }}>
                      <Typography variant="h6" component="h2">
                        Change Password
                      </Typography>
                    </Divider>
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Current Password"
                      name="currentPassword"
                      type="password"
                      value={formData.currentPassword}
                      onChange={handleChange}
                      required
                      inputProps={{
                        'aria-label': 'Current password',
                        'aria-required': 'true',
                      }}
                      onFocus={() => setFocusedField('currentPassword')}
                      onBlur={() => setFocusedField(null)}
                      helperText={focusedField === 'currentPassword' ? 'Enter your current password' : ' '}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="New Password"
                      name="newPassword"
                      type="password"
                      value={formData.newPassword}
                      onChange={handleChange}
                      inputProps={{
                        'aria-label': 'New password',
                      }}
                      onFocus={() => setFocusedField('newPassword')}
                      onBlur={() => setFocusedField(null)}
                      helperText={
                        focusedField === 'newPassword' 
                          ? 'Password must be at least 8 characters long'
                          : ' '
                      }
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Confirm New Password"
                      name="confirmPassword"
                      type="password"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      inputProps={{
                        'aria-label': 'Confirm new password',
                      }}
                      onFocus={() => setFocusedField('confirmPassword')}
                      onBlur={() => setFocusedField(null)}
                      helperText={
                        focusedField === 'confirmPassword'
                          ? 'Re-enter your new password'
                          : ' '
                      }
                    />
                  </Grid>
                </>
              )}

              <Grid item xs={12}>
                <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                  {!isEditing ? (
                    <Tooltip title="Edit profile information">
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={() => setIsEditing(true)}
                        startIcon={<EditIcon />}
                        aria-label="Edit profile"
                      >
                        Edit Profile
                      </Button>
                    </Tooltip>
                  ) : (
                    <>
                      <Tooltip title="Save changes (Ctrl/Cmd + S)">
                        <Button
                          variant="contained"
                          color="primary"
                          type="submit"
                          startIcon={<SaveIcon />}
                          aria-label="Save changes"
                        >
                          Save Changes
                        </Button>
                      </Tooltip>
                      <Tooltip title="Cancel editing (Esc)">
                        <Button
                          variant="outlined"
                          onClick={handleCancel}
                          startIcon={<CancelIcon />}
                          aria-label="Cancel editing"
                        >
                          Cancel
                        </Button>
                      </Tooltip>
                    </>
                  )}
                  <Tooltip title="Need help? Contact support">
                    <IconButton
                      aria-label="Help"
                      onClick={() => window.open('/help', '_blank')}
                      size="small"
                    >
                      <HelpIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Grid>
            </Grid>
          </form>
        </CardContent>
      </Card>

      <ConfirmDialog
        open={confirmDialog.open}
        title={confirmDialog.title}
        message={confirmDialog.message}
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog(prev => ({ ...prev, open: false }))}
      />

      {/* Screen reader only instructions */}
      <ScreenReaderOnly>
        <div role="note">
          Press Escape to cancel editing. Press Control or Command plus S to save changes.
          All form fields are required unless marked as optional.
        </div>
      </ScreenReaderOnly>
    </Box>
  );
}

const ProfileClientWithErrorBoundary = withErrorBoundary(ProfileClient, {
  onError: (error, errorInfo) => {
    // Log error to your error reporting service
    console.error('Error in Profile:', error, errorInfo);
  }
});

export default ProfileClientWithErrorBoundary; 