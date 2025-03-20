'use client';

import React from 'react';
import { Box, Typography, Button, Paper, Alert } from '@mui/material';
import { logger } from '@/lib/services/logging';

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  level?: 'page' | 'layout' | 'component';
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

/**
 * Enhanced Error Boundary component for handling React component errors
 * 
 * Features:
 * - Catches JavaScript errors in child component tree
 * - Logs errors to a logging service
 * - Displays a customizable fallback UI
 * - Supports different error levels (page, layout, component)
 * - Development mode error details
 * 
 * @example
 * ```tsx
 * <ErrorBoundary level="component" onError={handleError}>
 *   <MyComponent />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Log the error
    logger.error('React Error Boundary caught an error', {
      level: this.props.level || 'component',
      error: {
        message: error.message,
        stack: error.stack,
      },
      componentStack: errorInfo.componentStack,
    });

    // Call onError prop if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  renderFallback() {
    if (this.props.fallback) {
      return this.props.fallback;
    }

    const { level = 'component' } = this.props;
    const titles = {
      page: 'Page Error',
      layout: 'Application Error',
      component: 'Something went wrong',
    };

    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: level === 'page' ? '100vh' : 'auto',
          p: 3,
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            maxWidth: 600,
            width: '100%',
            textAlign: 'center',
          }}
        >
          <Typography variant="h4" component="h1" gutterBottom>
            {titles[level]}
          </Typography>
          
          <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
            {this.state.error?.message || 'An unexpected error occurred'}
          </Alert>

          <Typography variant="body1" color="text.secondary" paragraph>
            We apologize for the inconvenience. Please try again or contact support if the problem persists.
          </Typography>

          {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
            <Box sx={{ mt: 2, textAlign: 'left' }}>
              <Typography variant="subtitle2" color="error">
                Error Details:
              </Typography>
              <Typography
                variant="body2"
                component="pre"
                sx={{
                  backgroundColor: 'error.light',
                  color: 'error.contrastText',
                  p: 2,
                  borderRadius: 1,
                  overflow: 'auto',
                  maxHeight: '200px',
                }}
              >
                {this.state.error?.stack}
                {'\n'}
                {this.state.errorInfo.componentStack}
              </Typography>
            </Box>
          )}

          <Button
            variant="contained"
            color="primary"
            onClick={this.handleRetry}
            sx={{ mt: 2 }}
          >
            Try Again
          </Button>
        </Paper>
      </Box>
    );
  }

  render() {
    if (this.state.hasError) {
      return this.renderFallback();
    }

    return this.props.children;
  }
}

/**
 * HOC to wrap components with ErrorBoundary
 */
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  return function WithErrorBoundary(props: P) {
    return (
      <ErrorBoundary {...errorBoundaryProps}>
        <WrappedComponent {...props} />
      </ErrorBoundary>
    );
  };
} 