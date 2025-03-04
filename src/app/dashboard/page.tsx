'use client';

import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  useTheme
} from '@mui/material';
import {
  People,
  DoorFront,
  Security,
  Warning,
  CheckCircle,
  AccessTime
} from '@mui/icons-material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import DashboardCard from '@/components/dashboard/DashboardCard';
import AccessActivityList from '@/components/dashboard/AccessActivityList';
import AlertsList from '@/components/dashboard/AlertsList';
import { useAuth } from '@/providers/AuthProvider';

const mockData = {
  activeUsers: 156,
  doorsMonitored: 12,
  activeAlerts: 3,
  systemHealth: 98,
  accessAttempts: 1243,
  successRate: 99.2,
  accessHistory: [
    { time: '08:00', attempts: 45, successful: 44 },
    { time: '09:00', attempts: 62, successful: 60 },
    { time: '10:00', attempts: 78, successful: 76 },
    { time: '11:00', attempts: 56, successful: 54 },
    { time: '12:00', attempts: 89, successful: 87 },
    { time: '13:00', attempts: 68, successful: 66 },
  ]
};

export default function DashboardPage() {
  const theme = useTheme();
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <LinearProgress />
      </Box>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard Overview
      </Typography>

      <Grid container spacing={3}>
        {/* Overview Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="Active Users"
            value={mockData.activeUsers}
            icon={<People />}
            color={theme.palette.primary.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="Doors Monitored"
            value={mockData.doorsMonitored}
            icon={<DoorFront />}
            color={theme.palette.success.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="Active Alerts"
            value={mockData.activeAlerts}
            icon={<Warning />}
            color={theme.palette.warning.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="System Health"
            value={`${mockData.systemHealth}%`}
            icon={<CheckCircle />}
            color={theme.palette.info.main}
          />
        </Grid>

        {/* Access Statistics */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Access Activity
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={mockData.accessHistory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="attempts" fill={theme.palette.primary.main} name="Total Attempts" />
                  <Bar dataKey="successful" fill={theme.palette.success.main} name="Successful" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* System Status */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  CPU Usage
                </Typography>
                <LinearProgress variant="determinate" value={65} sx={{ mt: 1 }} />
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Memory Usage
                </Typography>
                <LinearProgress variant="determinate" value={45} sx={{ mt: 1 }} />
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Storage
                </Typography>
                <LinearProgress variant="determinate" value={32} sx={{ mt: 1 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Access Activity
              </Typography>
              <AccessActivityList />
            </CardContent>
          </Card>
        </Grid>

        {/* Active Alerts */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Alerts
              </Typography>
              <AlertsList />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
} 