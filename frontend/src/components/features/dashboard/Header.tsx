'use client';

import React from 'react';
import {
  AppBar,
  Avatar,
  Box,
  IconButton,
  Toolbar,
  Typography,
  useTheme
} from '@mui/material';
import { ExitToApp } from '@mui/icons-material';
import { User } from '@/types/user';

interface HeaderProps {
  user: User | null;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({ user, onLogout }) => {
  const theme = useTheme();

  return (
    <AppBar position="static" sx={{ mb: 3, bgcolor: 'background.paper' }}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1, color: 'text.primary' }}>
          CernoID Access Control
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body1" sx={{ color: 'text.primary' }}>
            {user?.name}
          </Typography>
          <Avatar
            alt={user?.name || 'User'}
            sx={{ width: 32, height: 32 }}
          >
            {user?.name?.[0] || 'U'}
          </Avatar>
          <IconButton onClick={onLogout} color="default">
            <ExitToApp />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
}; 