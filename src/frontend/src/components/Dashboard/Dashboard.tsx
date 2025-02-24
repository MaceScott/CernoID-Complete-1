import React, { useEffect, useState } from 'react';
import {
    Box,
    Grid,
    Paper,
    Typography,
    CircularProgress,
    Card,
    CardContent,
    useTheme
} from '@mui/material';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    LineChart,
    Line
} from 'recharts';
import { useMetrics } from '../../hooks/useMetrics';

interface MetricCardProps {
    title: string;
    value: string | number;
    subtitle?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, subtitle }) => (
    <Card>
        <CardContent>
            <Typography 
                color="textSecondary" 
                gutterBottom
            >
                {title}
            </Typography>
            <Typography 
                variant="h4" 
                component="div"
            >
                {value}
            </Typography>
            {subtitle && (
                <Typography 
                    color="textSecondary" 
                    sx={{ mt: 1 }}
                >
                    {subtitle}
                </Typography>
            )}
        </CardContent>
    </Card>
);

export const Dashboard: React.FC = () => {
    const theme = useTheme();
    const { metrics, loading, error } = useMetrics();
    const [chartData, setChartData] = useState<any[]>([]);

    useEffect(() => {
        if (metrics) {
            // Transform metrics data for charts
            setChartData(metrics.hourly_data || []);
        }
    }, [metrics]);

    if (loading) {
        return (
            <Box 
                sx={{ 
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center',
                    height: '100vh' 
                }}
            >
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Box sx={{ p: 3 }}>
                <Typography color="error">
                    Failed to load dashboard metrics
                </Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            <Typography 
                variant="h4" 
                sx={{ mb: 3 }}
            >
                Dashboard
            </Typography>

            <Grid container spacing={3}>
                {/* Metric Cards */}
                <Grid item xs={12} sm={6} md={3}>
                    <MetricCard
                        title="Total Requests"
                        value={metrics?.total_requests || 0}
                        subtitle="Last 24 hours"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <MetricCard
                        title="Success Rate"
                        value={`${metrics?.success_rate || 0}%`}
                        subtitle="Last 24 hours"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <MetricCard
                        title="Avg Response Time"
                        value={`${metrics?.avg_response_time || 0}ms`}
                        subtitle="Last hour"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <MetricCard
                        title="Active Users"
                        value={metrics?.active_users || 0}
                        subtitle="Current"
                    />
                </Grid>

                {/* Charts */}
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 2, height: 400 }}>
                        <Typography variant="h6" gutterBottom>
                            Request Volume
                        </Typography>
                        <ResponsiveContainer>
                            <BarChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="time" />
                                <YAxis />
                                <Tooltip />
                                <Bar 
                                    dataKey="requests" 
                                    fill={theme.palette.primary.main} 
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </Paper>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 2, height: 400 }}>
                        <Typography variant="h6" gutterBottom>
                            Response Times
                        </Typography>
                        <ResponsiveContainer>
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="time" />
                                <YAxis />
                                <Tooltip />
                                <Line 
                                    type="monotone"
                                    dataKey="response_time"
                                    stroke={theme.palette.secondary.main}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
}; 