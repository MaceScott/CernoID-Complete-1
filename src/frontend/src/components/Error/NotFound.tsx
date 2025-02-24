import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Button,
    Typography,
    Container,
    Paper
} from '@mui/material';
import {
    Home as HomeIcon,
    ArrowBack as ArrowBackIcon
} from '@mui/icons-material';

export const NotFound: React.FC = () => {
    const navigate = useNavigate();

    return (
        <Container maxWidth="sm">
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: '80vh'
                }}
            >
                <Paper
                    sx={{
                        p: 4,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        textAlign: 'center'
                    }}
                >
                    <Typography
                        variant="h1"
                        color="primary"
                        sx={{ 
                            fontSize: '6rem',
                            fontWeight: 'bold',
                            mb: 2
                        }}
                    >
                        404
                    </Typography>

                    <Typography variant="h5" gutterBottom>
                        Page Not Found
                    </Typography>

                    <Typography
                        variant="body1"
                        color="text.secondary"
                        sx={{ mb: 4 }}
                    >
                        The page you're looking for doesn't exist or has been moved.
                    </Typography>

                    <Box sx={{ display: 'flex', gap: 2 }}>
                        <Button
                            variant="contained"
                            startIcon={<HomeIcon />}
                            onClick={() => navigate('/')}
                        >
                            Go Home
                        </Button>
                        <Button
                            variant="outlined"
                            startIcon={<ArrowBackIcon />}
                            onClick={() => navigate(-1)}
                        >
                            Go Back
                        </Button>
                    </Box>
                </Paper>
            </Box>
        </Container>
    );
}; 