'use client';

import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  useTheme,
  Button,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Brightness4,
  Brightness7,
  AccountCircle,
  Settings,
  Notifications,
} from '@mui/icons-material';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';

interface TopBarProps {
  onSidebarToggle?: () => void;
  showMenuButton?: boolean;
  onThemeToggle: () => void;
  isDarkMode: boolean;
}

export const TopBar = ({
  onSidebarToggle,
  showMenuButton = true,
  onThemeToggle,
  isDarkMode,
}: TopBarProps) => {
  const theme = useTheme();
  const { user, logout } = useAuth();
  const router = useRouter();
  const [isLoggingOut, setIsLoggingOut] = React.useState(false);

  const handleLogout = async () => {
    try {
      setIsLoggingOut(true);
      await logout();
      router.push('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    <AppBar 
      position="fixed" 
      sx={{
        zIndex: theme.zIndex.drawer + 1,
        backgroundColor: theme.palette.background.paper,
        color: theme.palette.text.primary,
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {showMenuButton && (
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={onSidebarToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
        </Box>

        {/* Business Name - Centered */}
        <Typography
          variant="h5"
          component="h1"
          sx={{
            position: 'absolute',
            left: '50%',
            transform: 'translateX(-50%)',
            fontWeight: 600,
            letterSpacing: '0.05em',
            color: theme.palette.primary.main,
          }}
        >
          CernoID Security
        </Typography>

        {/* Right-side controls */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Toggle dark mode">
            <IconButton onClick={onThemeToggle} color="inherit">
              {isDarkMode ? <Brightness7 /> : <Brightness4 />}
            </IconButton>
          </Tooltip>

          {user && (
            <>
              <Tooltip title="Notifications">
                <IconButton color="inherit">
                  <Notifications />
                </IconButton>
              </Tooltip>

              <Tooltip title="Settings">
                <IconButton 
                  color="inherit"
                  onClick={() => router.push('/dashboard/settings')}
                >
                  <Settings />
                </IconButton>
              </Tooltip>

              <Box sx={{ display: 'flex', alignItems: 'center', ml: 2 }}>
                <IconButton
                  color="inherit"
                  onClick={() => router.push('/dashboard/profile')}
                >
                  <AccountCircle />
                </IconButton>
                <Button
                  variant="outlined"
                  color="inherit"
                  onClick={handleLogout}
                  disabled={isLoggingOut}
                  sx={{ ml: 1, minWidth: 100 }}
                >
                  {isLoggingOut ? (
                    <CircularProgress size={20} color="inherit" />
                  ) : (
                    'Logout'
                  )}
                </Button>
              </Box>
            </>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
}; 