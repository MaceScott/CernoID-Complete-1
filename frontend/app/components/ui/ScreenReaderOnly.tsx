import { Box, BoxProps } from '@mui/material';
import { ReactNode } from 'react';

interface ScreenReaderOnlyProps extends BoxProps {
  children: ReactNode;
}

export function ScreenReaderOnly({ children, ...props }: ScreenReaderOnlyProps) {
  return (
    <Box
      {...props}
      sx={{
        position: 'absolute',
        width: '1px',
        height: '1px',
        padding: '0',
        margin: '-1px',
        overflow: 'hidden',
        clip: 'rect(0, 0, 0, 0)',
        whiteSpace: 'nowrap',
        border: '0',
        ...props.sx,
      }}
    >
      {children}
    </Box>
  );
} 