'use client';

import React from 'react';
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
  Collapse,
} from '@mui/material';
import {
  ChevronLeft,
  ChevronRight,
  ExpandLess,
  ExpandMore,
} from '@mui/icons-material';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { motion } from 'framer-motion';
import { navigationConfig, getNavigationItems } from '@/lib/navigation/config';
import type { User } from '@/lib/auth/types';

const MotionBox = motion(Box);

const drawerWidth = 240;

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useAuth();
  const [expandedItems, setExpandedItems] = React.useState<Set<string>>(new Set());

  // Get filtered navigation items based on user role and permissions
  const navigationItems = React.useMemo(() => {
    if (!user) return [];
    return getNavigationItems(user.role, user.permissions);
  }, [user]);

  const handleItemClick = (path: string) => {
    router.push(path);
    if (isMobile) {
      onClose();
    }
  };

  const handleExpandClick = (path: string) => {
    setExpandedItems(prev => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const renderNavigationItem = (item: typeof navigationConfig[0], level: number = 0) => {
    const isExpanded = expandedItems.has(item.path);
    const isActive = pathname === item.path;
    const children = item.children as typeof navigationConfig | undefined;
    const hasChildren = Array.isArray(children) && children.length > 0;
    const Icon = item.icon;

    return (
      <React.Fragment key={item.path}>
        <ListItem disablePadding>
          <ListItemButton
            onClick={() => hasChildren ? handleExpandClick(item.path) : handleItemClick(item.path)}
            sx={{
              pl: level * 2,
              backgroundColor: isActive ? theme.palette.action.selected : 'transparent',
            }}
          >
            <ListItemIcon>
              <Icon />
            </ListItemIcon>
            <ListItemText primary={item.title} />
            {hasChildren && (isExpanded ? <ExpandLess /> : <ExpandMore />)}
          </ListItemButton>
        </ListItem>
        {hasChildren && (
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {children.map(child => renderNavigationItem(child, level + 1))}
            </List>
          </Collapse>
        )}
      </React.Fragment>
    );
  };

  return (
    <Drawer
      variant={isMobile ? 'temporary' : 'permanent'}
      open={open}
      onClose={onClose}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          borderRight: `1px solid ${theme.palette.divider}`,
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', p: 1 }}>
        <IconButton onClick={onClose}>
          {theme.direction === 'ltr' ? <ChevronLeft /> : <ChevronRight />}
        </IconButton>
      </Box>
      <Divider />
      <List>
        {navigationItems.map(item => renderNavigationItem(item))}
      </List>
    </Drawer>
  );
} 