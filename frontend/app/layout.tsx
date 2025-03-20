import { Inter } from 'next/font/google';
import { ThemeProvider } from './providers/ThemeProvider';
import { AuthProvider } from './providers/AuthProvider';
import { WebSocketProvider } from './providers/WebSocketProvider';
import { ServiceProvider } from './providers/ServiceProvider';
import './globals.css';
import { ErrorBoundary } from '@/components/shared/feedback';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'CernoID Security System',
  description: 'Advanced security and surveillance system with face recognition capabilities',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ErrorBoundary>
          <ServiceProvider>
            <ThemeProvider>
              <AuthProvider>
                <WebSocketProvider>
                  {children}
                </WebSocketProvider>
              </AuthProvider>
            </ThemeProvider>
          </ServiceProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
} 