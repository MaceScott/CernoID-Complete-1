import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
    List,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Divider,
    Box,
    Typography
} from '@mui/material';
import {
    Dashboard,
    Security,
    People,
    Settings,
    Camera,
    Notifications
} from '@mui/icons-material';
import { useApp } from '../../context/AppContext';

interface NavigationProps {
    onItemClick?: () => void;
}

export const Navigation: React.FC<NavigationProps> = ({ onItemClick }) => {
    const navigate = useNavigate();
    const { state: { user } } = useApp();

    const handleNavigation = (path: string) => {
        navigate(path);
        onItemClick?.();
    };

    const menuItems = [
        {
            text: 'Dashboard',
            icon: <Dashboard />,
            path: '/dashboard',
            show: true
        },
        {
            text: 'Security',
            icon: <Security />,
            path: '/security',
            show: true
        },
        {
            text: 'Cameras',
            icon: <Camera />,
            path: '/cameras',
            show: true
        },
        {
            text: 'Alerts',
            icon: <Notifications />,
            path: '/alerts',
            show: true
        },
        {
            text: 'Users',
            icon: <People />,
            path: '/users',
            show: user?.isAdmin
        },
        {
            text: 'Settings',
            icon: <Settings />,
            path: '/settings',
            show: user?.isAdmin
        }
    ];

    return (
        <Box sx={{ width: 240 }}>
            <Typography variant="h6" sx={{ px: 2, py: 2 }}>
                CernoID Security
            </Typography>
            <Divider />
            <List>
                {menuItems.filter(item => item.show).map((item) => (
                    <ListItemButton
                        key={item.text}
                        onClick={() => handleNavigation(item.path)}
                    >
                        <ListItemIcon>{item.icon}</ListItemIcon>
                        <ListItemText primary={item.text} />
                    </ListItemButton>
                ))}
            </List>
        </Box>
    );
}; 