import React, { useState } from 'react';
import {
  AppBar,
  Avatar,
  Badge,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Toolbar,
  Typography,
  useTheme
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications,
  Settings,
  Person,
  ExitToApp
} from '@mui/icons-material';
import { useAuth } from '@/hooks/useAuth';

interface HeaderProps {
  onToggleSidebar?: () => void;
}

export default function DashboardHeader({ onToggleSidebar }: HeaderProps) {
  const theme = useTheme();
  const { user, logout } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notificationAnchor, setNotificationAnchor] = useState<null | HTMLElement>(null);

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleNotifications = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchor(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
    setNotificationAnchor(null);
  };

  return (
    <AppBar position="fixed" sx={{ zIndex: theme.zIndex.drawer + 1 }}>
      <Toolbar>
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={onToggleSidebar}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>

        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
          Access Control System
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <IconButton color="inherit" onClick={handleNotifications}>
            <Badge badgeContent={4} color="error">
              <Notifications />
            </Badge>
          </IconButton>

          <IconButton color="inherit" onClick={handleMenu}>
            <Avatar
              alt={user?.name || 'User'}
              src={user?.avatar}
              sx={{ width: 32, height: 32 }}
            />
          </IconButton>
        </Box>

        <Menu
          id="menu-appbar"
          anchorEl={anchorEl}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          keepMounted
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          open={Boolean(anchorEl)}
          onClose={handleClose}
        >
          <MenuItem onClick={handleClose}>
            <Person sx={{ mr: 1 }} /> Profile
          </MenuItem>
          <MenuItem onClick={handleClose}>
            <Settings sx={{ mr: 1 }} /> Settings
          </MenuItem>
          <MenuItem onClick={logout}>
            <ExitToApp sx={{ mr: 1 }} /> Logout
          </MenuItem>
        </Menu>

        <Menu
          id="notifications-menu"
          anchorEl={notificationAnchor}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          keepMounted
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          open={Boolean(notificationAnchor)}
          onClose={handleClose}
        >
          <MenuItem onClick={handleClose}>
            New access request at Main Entrance
          </MenuItem>
          <MenuItem onClick={handleClose}>
            Security alert: Multiple failed attempts
          </MenuItem>
          <MenuItem onClick={handleClose}>
            System update available
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
} 