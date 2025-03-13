'use client';

import React from 'react';
import {
  Breadcrumbs as MuiBreadcrumbs,
  Link,
  Typography,
  Box,
  useTheme,
} from '@mui/material';
import { usePathname } from 'next/navigation';
import NextLink from 'next/link';
import { NavigateNext as NavigateNextIcon } from '@mui/icons-material';

const routeNameMap: Record<string, string> = {
  dashboard: 'Dashboard',
  cameras: 'Cameras',
  recognition: 'Recognition',
  settings: 'Settings',
  admin: 'Admin Panel',
  profile: 'Profile',
  'forgot-password': 'Forgot Password',
  register: 'Register',
  login: 'Login',
  users: 'Users',
  security: 'Security',
};

// Map of dynamic route parameters to their display names
const dynamicRouteMap: Record<string, (param: string) => string> = {
  userId: (id) => `User ${id}`,
  cameraId: (id) => `Camera ${id}`,
  eventId: (id) => `Event ${id}`,
};

export default function Breadcrumbs() {
  const pathname = usePathname();
  const theme = useTheme();

  const getPathParts = () => {
    const parts = pathname.split('/').filter(Boolean);
    const breadcrumbs = parts.map((part, index) => {
      const path = `/${parts.slice(0, index + 1).join('/')}`;
      let name = routeNameMap[part] || part.charAt(0).toUpperCase() + part.slice(1);
      
      // Handle dynamic routes
      if (part.startsWith('[') && part.endsWith(']')) {
        const paramName = part.slice(1, -1);
        const paramValue = parts[index + 1];
        if (dynamicRouteMap[paramName] && paramValue) {
          name = dynamicRouteMap[paramName](paramValue);
          // Skip the next part since we've handled it
          return {
            name,
            path: `/${parts.slice(0, index + 2).join('/')}`,
            isLast: index + 1 === parts.length - 1,
          };
        }
      }

      return {
        name,
        path,
        isLast: index === parts.length - 1,
      };
    });

    return breadcrumbs;
  };

  const pathParts = getPathParts();

  if (pathParts.length === 0) {
    return null;
  }

  return (
    <Box
      sx={{
        padding: theme.spacing(2),
        backgroundColor: theme.palette.background.paper,
        borderBottom: `1px solid ${theme.palette.divider}`,
      }}
    >
      <MuiBreadcrumbs
        separator={<NavigateNextIcon fontSize="small" />}
        aria-label="breadcrumb"
      >
        <Link
          component={NextLink}
          href="/"
          underline="hover"
          color="inherit"
          sx={{
            display: 'flex',
            alignItems: 'center',
          }}
        >
          Home
        </Link>
        {pathParts.map(({ name, path, isLast }) =>
          isLast ? (
            <Typography
              key={path}
              color="primary"
              sx={{ fontWeight: 'medium' }}
            >
              {name}
            </Typography>
          ) : (
            <Link
              key={path}
              component={NextLink}
              href={path}
              underline="hover"
              color="inherit"
            >
              {name}
            </Link>
          )
        )}
      </MuiBreadcrumbs>
    </Box>
  );
} 