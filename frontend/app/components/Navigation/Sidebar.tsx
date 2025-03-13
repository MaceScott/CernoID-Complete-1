'use client';

import React, { useState } from 'react';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Tooltip,
  Divider,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  ChevronLeft,
  ChevronRight,
  Dashboard,
  Videocam,
  Settings,
  AdminPanelSettings,
  Face,
  GridView,
  Person,
  Menu as MenuIcon,
  Security,
} from '@mui/icons-material';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { motion } from 'framer-motion';

const MotionBox = motion(Box);

interface NavigationItem {
  title: string;
  path: string;
  icon: React.ReactNode;
  roles?: string[];
  children?: NavigationItem[];
}

const navigationItems: NavigationItem[] = [
  { title: 'Dashboard', path: '/dashboard', icon: <Dashboard /> },
  { title: 'Cameras', path: '/cameras', icon: <Videocam /> },
  { title: 'Recognition', path: '/recognition', icon: <Face /> },
  { title: 'Settings', path: '/settings', icon: <Settings /> },
  {
    title: 'Admin Panel',
    path: '/admin',
    icon: <AdminPanelSettings />,
    roles: ['admin'],
    children: [
      { title: 'Users', path: '/admin/users', icon: <Person /> },
      { title: 'Security', path: '/admin/security', icon: <Security /> },
    ],
  },
  { title: 'Profile', path: '/profile', icon: <Person /> },
];

const drawerWidth = 240;

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  const theme = useTheme();
  const router = useRouter();
  const pathname = usePathname();
  const { user } = useAuth();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Auto-collapse on mobile
  React.useEffect(() => {
    if (isMobile) {
      onClose();
    }
  }, [isMobile, onClose]);

  const handleDrawerToggle = () => {
    onClose();
  };

  const filteredItems = navigationItems.filter(
    (item) => !item.roles || (user?.role && item.roles.includes(user.role))
  );

  return (
    <Box
      component={motion.nav}
      initial={false}
      animate={{ width: open ? drawerWidth : theme.spacing(7) }}
      transition={{ duration: 0.2 }}
      sx={{
        position: 'fixed',
        height: '100vh',
        zIndex: theme.zIndex.drawer,
      }}
    >
      <Drawer
        variant="permanent"
        sx={{
          width: open ? drawerWidth : theme.spacing(7),
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: open ? drawerWidth : theme.spacing(7),
            boxSizing: 'border-box',
            borderRight: `1px solid ${theme.palette.divider}`,
            backgroundColor: theme.palette.background.paper,
            transition: theme.transitions.create(['width'], {
              duration: theme.transitions.duration.standard,
            }),
            overflowX: 'hidden',
          },
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: open ? 'flex-end' : 'center',
            padding: theme.spacing(1),
          }}
        >
          <IconButton onClick={handleDrawerToggle}>
            {open ? <ChevronLeft /> : <MenuIcon />}
          </IconButton>
        </Box>
        <Divider />
        <List>
          {filteredItems.map((item) => {
            const isActive = pathname === item.path || pathname.startsWith(`${item.path}/`);
            const hasChildren = Array.isArray(item.children) && item.children.length > 0;
            
            return (
              <React.Fragment key={item.path}>
                <ListItem disablePadding>
                  <Tooltip
                    title={!open ? item.title : ''}
                    placement="right"
                    arrow
                  >
                    <ListItemButton
                      onClick={() => router.push(item.path)}
                      sx={{
                        minHeight: 48,
                        justifyContent: open ? 'initial' : 'center',
                        backgroundColor: isActive
                          ? theme.palette.action.selected
                          : 'transparent',
                        '&:hover': {
                          backgroundColor: theme.palette.action.hover,
                        },
                      }}
                    >
                      <ListItemIcon
                        sx={{
                          minWidth: 0,
                          mr: open ? 2 : 'auto',
                          justifyContent: 'center',
                          color: isActive
                            ? theme.palette.primary.main
                            : 'inherit',
                        }}
                      >
                        {item.icon}
                      </ListItemIcon>
                      <ListItemText
                        primary={item.title}
                        sx={{
                          opacity: open ? 1 : 0,
                          color: isActive
                            ? theme.palette.primary.main
                            : 'inherit',
                        }}
                      />
                    </ListItemButton>
                  </Tooltip>
                </ListItem>
                {hasChildren && open && item.children && (
                  <List sx={{ pl: 2 }}>
                    {item.children.map((child) => {
                      const isChildActive = pathname === child.path;
                      return (
                        <ListItem key={child.path} disablePadding>
                          <Tooltip
                            title={!open ? child.title : ''}
                            placement="right"
                            arrow
                          >
                            <ListItemButton
                              onClick={() => router.push(child.path)}
                              sx={{
                                minHeight: 48,
                                justifyContent: open ? 'initial' : 'center',
                                backgroundColor: isChildActive
                                  ? theme.palette.action.selected
                                  : 'transparent',
                                '&:hover': {
                                  backgroundColor: theme.palette.action.hover,
                                },
                              }}
                            >
                              <ListItemIcon
                                sx={{
                                  minWidth: 0,
                                  mr: open ? 2 : 'auto',
                                  justifyContent: 'center',
                                  color: isChildActive
                                    ? theme.palette.primary.main
                                    : 'inherit',
                                }}
                              >
                                {child.icon}
                              </ListItemIcon>
                              <ListItemText
                                primary={child.title}
                                sx={{
                                  opacity: open ? 1 : 0,
                                  color: isChildActive
                                    ? theme.palette.primary.main
                                    : 'inherit',
                                }}
                              />
                            </ListItemButton>
                          </Tooltip>
                        </ListItem>
                      );
                    })}
                  </List>
                )}
              </React.Fragment>
            );
          })}
        </List>
      </Drawer>
    </Box>
  );
} 