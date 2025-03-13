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

  const handleLogout = async () => {
    await logout();
    router.push('/login');
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
                  onClick={() => router.push('/settings')}
                >
                  <Settings />
                </IconButton>
              </Tooltip>

              <Box sx={{ display: 'flex', alignItems: 'center', ml: 2 }}>
                <IconButton
                  color="inherit"
                  onClick={() => router.push('/profile')}
                >
                  <AccountCircle />
                </IconButton>
                <Button
                  variant="outlined"
                  color="inherit"
                  onClick={handleLogout}
                  sx={{ ml: 1 }}
                >
                  Logout
                </Button>
              </Box>
            </>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
}; 