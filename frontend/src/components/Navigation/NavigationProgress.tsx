import React, { useState, useEffect } from 'react';
import { useLocation, useNavigationType } from 'react-router-dom';
import { LinearProgress, Box } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';

export const NavigationProgress: React.FC = () => {
    const location = useLocation();
    const navigationType = useNavigationType();
    const [isNavigating, setIsNavigating] = useState(false);
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        let timer: NodeJS.Timeout;
        
        const startNavigation = () => {
            setIsNavigating(true);
            setProgress(0);
            
            const increment = () => {
                setProgress(prev => {
                    if (prev >= 90) return prev;
                    return prev + (90 - prev) * 0.1;
                });
                
                timer = setTimeout(increment, 100);
            };
            
            increment();
        };
        
        const completeNavigation = () => {
            setProgress(100);
            setTimeout(() => {
                setIsNavigating(false);
                setProgress(0);
            }, 200);
        };

        startNavigation();
        return () => {
            clearTimeout(timer);
            completeNavigation();
        };
    }, [location.pathname, navigationType]);

    return (
        <AnimatePresence>
            {isNavigating && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                >
                    <Box
                        sx={{
                            position: 'fixed',
                            top: 0,
                            left: 0,
                            right: 0,
                            zIndex: 9999
                        }}
                    >
                        <LinearProgress
                            variant="determinate"
                            value={progress}
                            sx={{
                                height: 2,
                                '& .MuiLinearProgress-bar': {
                                    transition: 'transform 0.1s linear'
                                }
                            }}
                        />
                    </Box>
                </motion.div>
            )}
        </AnimatePresence>
    );
}; 