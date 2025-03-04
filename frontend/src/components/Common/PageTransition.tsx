import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { Box } from '@mui/material';

interface PageTransitionProps {
    children: React.ReactNode;
}

export const PageTransition: React.FC<PageTransitionProps> = ({ children }) => {
    const location = useLocation();

    return (
        <AnimatePresence mode="wait">
            <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{
                    duration: 0.3,
                    ease: 'easeInOut'
                }}
            >
                <Box sx={{ position: 'relative' }}>
                    {children}
                </Box>
            </motion.div>
        </AnimatePresence>
    );
};

export const FadeTransition: React.FC<{
    children: React.ReactNode;
    show: boolean;
}> = ({ children, show }) => (
    <AnimatePresence>
        {show && (
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
            >
                {children}
            </motion.div>
        )}
    </AnimatePresence>
);

export const SlideTransition: React.FC<{
    children: React.ReactNode;
    show: boolean;
    direction?: 'left' | 'right' | 'up' | 'down';
}> = ({ children, show, direction = 'right' }) => {
    const variants = {
        left: { x: -50 },
        right: { x: 50 },
        up: { y: -50 },
        down: { y: 50 }
    };

    return (
        <AnimatePresence>
            {show && (
                <motion.div
                    initial={{ 
                        opacity: 0,
                        ...variants[direction]
                    }}
                    animate={{ 
                        opacity: 1,
                        x: 0,
                        y: 0
                    }}
                    exit={{
                        opacity: 0,
                        ...variants[direction]
                    }}
                    transition={{ duration: 0.3 }}
                >
                    {children}
                </motion.div>
            )}
        </AnimatePresence>
    );
}; 