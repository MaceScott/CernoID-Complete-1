import React from 'react';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  useTheme
} from '@mui/material';
import {
  Dashboard,
  Security,
  People,
  DoorFront,
  VideoCamera,
  History,
  Settings,
  Assessment,
  NotificationsActive,
  Schedule
} from '@mui/icons-material';
import { useRouter, usePathname } from 'next/navigation';

const DRAWER_WIDTH = 240;

const menuItems = [
  { title: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
  { title: 'Access Control', icon: <Security />, path: '/dashboard/access' },
  { title: 'Users', icon: <People />, path: '/dashboard/users' },
  { title: 'Doors', icon: <DoorFront />, path: '/dashboard/doors' },
  { title: 'Cameras', icon: <VideoCamera />, path: '/dashboard/cameras' },
  { title: 'Access History', icon: <History />, path: '/dashboard/history' },
  { title: 'Schedules', icon: <Schedule />, path: '/dashboard/schedules' },
  { title: 'Reports', icon: <Assessment />, path: '/dashboard/reports' },
  { title: 'Alerts', icon: <NotificationsActive />, path: '/dashboard/alerts' },
  { title: 'Settings', icon: <Settings />, path: '/dashboard/settings' }
];

export default function DashboardSidebar() {
  const theme = useTheme();
  const router = useRouter();
  const pathname = usePathname();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          mt: 8,
          backgroundColor: theme.palette.background.default,
          borderRight: `1px solid ${theme.palette.divider}`
        },
      }}
    >
      <Box sx={{ overflow: 'auto', mt: 1 }}>
        <List>
          {menuItems.map((item, index) => (
            <React.Fragment key={item.title}>
              {index === 6 && <Divider sx={{ my: 1 }} />}
              <ListItem disablePadding>
                <ListItemButton
                  selected={pathname === item.path}
                  onClick={() => router.push(item.path)}
                  sx={{
                    '&.Mui-selected': {
                      backgroundColor: theme.palette.primary.main + '20',
                      '&:hover': {
                        backgroundColor: theme.palette.primary.main + '30',
                      },
                    },
                  }}
                >
                  <ListItemIcon
                    sx={{
                      color: pathname === item.path
                        ? theme.palette.primary.main
                        : theme.palette.text.secondary
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.title}
                    sx={{
                      color: pathname === item.path
                        ? theme.palette.primary.main
                        : theme.palette.text.primary
                    }}
                  />
                </ListItemButton>
              </ListItem>
            </React.Fragment>
          ))}
        </List>
      </Box>
    </Drawer>
  );
} 