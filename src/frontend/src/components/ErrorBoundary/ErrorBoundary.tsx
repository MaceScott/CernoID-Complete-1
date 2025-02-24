import React, { Component, ErrorInfo, ReactNode } from 'react';
import {
    Box,
    Paper,
    Typography,
    Button,
    Alert
} from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
    errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
        errorInfo: null
    };

    public static getDerivedStateFromError(error: Error): State {
        return {
            hasError: true,
            error,
            errorInfo: null
        };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        this.setState({
            error,
            errorInfo
        });

        // Log error to monitoring service
        console.error('Uncaught error:', error, errorInfo);
    }

    private handleRefresh = () => {
        window.location.reload();
    };

    public render() {
        if (this.state.hasError) {
            return (
                <Box sx={{ 
                    p: 3,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: '100vh'
                }}>
                    <Paper sx={{ p: 4, maxWidth: 600, width: '100%' }}>
                        <Typography variant="h4" gutterBottom>
                            Something went wrong
                        </Typography>

                        <Alert severity="error" sx={{ mb: 3 }}>
                            {this.state.error?.message || 'An unexpected error occurred'}
                        </Alert>

                        {process.env.NODE_ENV === 'development' && (
                            <Box 
                                component="pre"
                                sx={{ 
                                    p: 2,
                                    bgcolor: 'grey.100',
                                    borderRadius: 1,
                                    overflow: 'auto',
                                    mb: 3
                                }}
                            >
                                {this.state.error?.stack}
                                {this.state.errorInfo?.componentStack}
                            </Box>
                        )}

                        <Button
                            variant="contained"
                            startIcon={<RefreshIcon />}
                            onClick={this.handleRefresh}
                        >
                            Refresh Page
                        </Button>
                    </Paper>
                </Box>
            );
        }

        return this.props.children;
    }
} 