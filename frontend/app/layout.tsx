// Remove or comment out the 'use client' directive if it exists
// import type { Metadata } from 'next';
import './globals.css';
import { ThemeProvider } from './theme/ThemeProvider';
import { DashboardLayout } from './components/Layout/DashboardLayout';
import { AppRouterCacheProvider } from '@mui/material-nextjs/v14-appRouter';
import { usePathname } from 'next/navigation';
import type { Metadata } from 'next';
import { AuthProvider } from './providers/AuthProvider';

// Routes that don't use the app layout
const publicRoutes = ['/login', '/register', '/forgot-password'];

export const metadata: Metadata = {
  title: 'CernoID - Secure Access Control',
  description: 'Advanced facial recognition and access control system',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isPublicRoute = publicRoutes.includes(pathname);

  return (
    <html lang="en">
      <body>
        <AppRouterCacheProvider>
          <ThemeProvider>
            <AuthProvider>
              {isPublicRoute ? children : <DashboardLayout>{children}</DashboardLayout>}
            </AuthProvider>
          </ThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
} 