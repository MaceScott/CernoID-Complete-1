import { Box, CssBaseline, ThemeProvider } from '@mui/material';
import DashboardHeader from '@/components/dashboard/Header';
import DashboardSidebar from '@/components/dashboard/Sidebar';
import { theme } from '@/theme';
import { AuthProvider } from '@/providers/AuthProvider';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Box sx={{ display: 'flex', minHeight: '100vh' }}>
          <DashboardHeader />
          <DashboardSidebar />
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              p: 3,
              pt: 10,
              backgroundColor: 'background.default'
            }}
          >
            {children}
          </Box>
        </Box>
      </AuthProvider>
    </ThemeProvider>
  );
} 