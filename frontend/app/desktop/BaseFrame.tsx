import { ReactNode } from 'react';
import { Box, Container, Paper, Typography } from '@mui/material';

interface BaseFrameProps {
  children: ReactNode;
  title: string;
}

export function BaseFrame({ children, title }: BaseFrameProps) {
  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          {title}
        </Typography>
        <Box sx={{ mt: 3 }}>
          {children}
        </Box>
      </Paper>
    </Container>
  );
} 