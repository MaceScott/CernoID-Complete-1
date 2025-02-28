import React from 'react';
import { 
    AppBar, 
    Toolbar, 
    IconButton, 
    Typography, 
    Button,
    Box,
    Drawer,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    ListItemButton,
    useMediaQuery,
    useTheme
} from '@mui/material';
import {
    Menu as MenuIcon,
    Dashboard as DashboardIcon,
    Face as FaceIcon,
    People as PeopleIcon,
    Settings as SettingsIcon,
    ExitToApp as LogoutIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

interface NavigationProps {
    open: boolean;
    onClose: () => void;
    onOpen: () => void;
}

export const Navigation: React.FC<NavigationProps> = ({ open, onClose, onOpen }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));

    const menuItems = [
        { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
        { text: 'Recognition', icon: <FaceIcon />, path: '/recognition' },
        { text: 'Users', icon: <PeopleIcon />, path: '/users' },
        { text: 'Settings', icon: <SettingsIcon />, path: '/settings' }
    ];

    const handleNavigation = (path: string) => {
        navigate(path);
        if (isMobile) {
            onClose();
        }
    };

    const drawer = (
        <Box sx={{ width: 250 }}>
            <List>
                {menuItems.map((item) => (
                    <ListItemButton 
                        component="button"
                        key={item.text}
                        onClick={() => handleNavigation(item.path)}
                        sx={{
                            '&:hover': {
                                backgroundColor: theme.palette.action.hover
                            }
                        }}
                    >
                        <ListItemIcon sx={{ color: theme.palette.primary.main }}>
                            {item.icon}
                        </ListItemIcon>
                        <ListItemText primary={item.text} />
                    </ListItemButton>
                ))}
            </List>
        </Box>
    );

    return (
        <>
            <AppBar position="fixed">
                <Toolbar>
                    <IconButton
                        color="inherit"
                        edge="start"
                        onClick={onOpen}
                        sx={{ mr: 2, display: { md: 'none' } }}
                    >
                        <MenuIcon />
                    </IconButton>
                    
                    <Typography 
                        variant="h6" 
                        component="div" 
                        sx={{ flexGrow: 1 }}
                    >
                        CernoID
                    </Typography>

                    {user && (
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Typography 
                                sx={{ 
                                    mr: 2,
                                    display: { xs: 'none', sm: 'block' } 
                                }}
                            >
                                {user.username}
                            </Typography>
                            <Button 
                                color="inherit"
                                onClick={logout}
                                startIcon={<LogoutIcon />}
                            >
                                Logout
                            </Button>
                        </Box>
                    )}
                </Toolbar>
            </AppBar>

            <Drawer
                variant={isMobile ? "temporary" : "permanent"}
                open={isMobile ? open : true}
                onClose={onClose}
                sx={{
                    '& .MuiDrawer-paper': {
                        width: 250,
                        boxSizing: 'border-box',
                        marginTop: '64px',
                        height: 'calc(100% - 64px)'
                    }
                }}
            >
                {drawer}
            </Drawer>
        </>
    );
}; 