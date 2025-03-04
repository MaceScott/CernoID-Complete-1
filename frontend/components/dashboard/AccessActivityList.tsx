'use client';

import React from 'react';
import {
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Typography,
  Chip,
  Box
} from '@mui/material';
import {
  CheckCircle,
  Cancel,
  Person
} from '@mui/icons-material';

const mockActivity = [
  {
    id: 1,
    user: 'John Smith',
    door: 'Main Entrance',
    time: '2 minutes ago',
    status: 'granted',
    distance: '1.2m'
  },
  {
    id: 2,
    user: 'Sarah Johnson',
    door: 'Server Room',
    time: '5 minutes ago',
    status: 'denied',
    distance: '3.5m'
  },
  {
    id: 3,
    user: 'Mike Wilson',
    door: 'Lab Access',
    time: '10 minutes ago',
    status: 'granted',
    distance: '0.8m'
  },
  {
    id: 4,
    user: 'Emily Brown',
    door: 'Main Entrance',
    time: '15 minutes ago',
    status: 'granted',
    distance: '1.1m'
  },
  {
    id: 5,
    user: 'Unknown',
    door: 'Side Entrance',
    time: '20 minutes ago',
    status: 'denied',
    distance: '4.2m'
  }
];

export default function AccessActivityList() {
  return (
    <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
      {mockActivity.map((activity) => (
        <ListItem
          key={activity.id}
          alignItems="flex-start"
          sx={{
            borderBottom: '1px solid',
            borderColor: 'divider',
            '&:last-child': {
              borderBottom: 'none'
            }
          }}
        >
          <ListItemAvatar>
            <Avatar
              sx={{
                bgcolor: activity.status === 'granted'
                  ? 'success.light'
                  : 'error.light'
              }}
            >
              {activity.status === 'granted' ? <CheckCircle /> : <Cancel />}
            </Avatar>
          </ListItemAvatar>
          <ListItemText
            primary={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="subtitle2">
                  {activity.user}
                </Typography>
                <Chip
                  size="small"
                  label={activity.status}
                  color={activity.status === 'granted' ? 'success' : 'error'}
                />
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ ml: 'auto' }}
                >
                  {activity.time}
                </Typography>
              </Box>
            }
            secondary={
              <React.Fragment>
                <Typography
                  component="span"
                  variant="body2"
                  color="text.primary"
                >
                  {activity.door}
                </Typography>
                {' — '}
                <Typography
                  component="span"
                  variant="body2"
                  color="text.secondary"
                >
                  Distance: {activity.distance}
                </Typography>
              </React.Fragment>
            }
          />
        </ListItem>
      ))}
    </List>
  );
} 