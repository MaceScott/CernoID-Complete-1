import React from 'react';
import {
    Box,
    Paper,
    Typography,
    Breadcrumbs,
    Link,
    useTheme
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

interface PageLayoutProps {
    title: string;
    breadcrumbs?: Array<{
        label: string;
        path?: string;
    }>;
    actions?: React.ReactNode;
    children: React.ReactNode;
}

export const PageLayout: React.FC<PageLayoutProps> = ({
    title,
    breadcrumbs,
    actions,
    children
}) => {
    const theme = useTheme();

    return (
        <Box>
            {/* Header */}
            <Box
                sx={{
                    mb: 3,
                    display: 'flex',
                    flexDirection: { xs: 'column', sm: 'row' },
                    justifyContent: 'space-between',
                    alignItems: { xs: 'flex-start', sm: 'center' },
                    gap: 2
                }}
            >
                <Box>
                    {breadcrumbs && (
                        <Breadcrumbs
                            sx={{ mb: 1 }}
                            aria-label="breadcrumb"
                        >
                            {breadcrumbs.map((crumb, index) => {
                                const isLast = index === breadcrumbs.length - 1;
                                
                                if (isLast || !crumb.path) {
                                    return (
                                        <Typography
                                            key={crumb.label}
                                            color="text.primary"
                                        >
                                            {crumb.label}
                                        </Typography>
                                    );
                                }

                                return (
                                    <Link
                                        key={crumb.label}
                                        component={RouterLink}
                                        to={crumb.path}
                                        color="inherit"
                                        underline="hover"
                                    >
                                        {crumb.label}
                                    </Link>
                                );
                            })}
                        </Breadcrumbs>
                    )}
                    <Typography variant="h4" component="h1">
                        {title}
                    </Typography>
                </Box>
                
                {actions && (
                    <Box sx={{ 
                        display: 'flex',
                        gap: 2,
                        alignItems: 'center'
                    }}>
                        {actions}
                    </Box>
                )}
            </Box>

            {/* Content */}
            <Paper
                sx={{
                    p: 3,
                    height: '100%',
                    backgroundColor: theme.palette.background.paper
                }}
            >
                {children}
            </Paper>
        </Box>
    );
}; 