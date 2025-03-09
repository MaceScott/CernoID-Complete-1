'use client';

import { AppBar, Toolbar, Typography, IconButton, Box } from '@mui/material';
import { Menu as MenuIcon, Logout as LogoutIcon } from '@mui/icons-material';
import { useAuth } from '@/app/providers/AuthProvider';

interface HeaderProps {
  onMenuClick: () => void;
}

export const Header = ({ onMenuClick }: HeaderProps) => {
  const { logout } = useAuth();

  return (
    <AppBar position="fixed">
      <Toolbar>
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={onMenuClick}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          CernoID Security System
        </Typography>
        <Box>
          <IconButton color="inherit" onClick={logout} title="Logout">
            <LogoutIcon />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
}; 