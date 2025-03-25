'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';

interface AdminGuardProps {
  children: React.ReactNode;
  session?: any; // Add session prop
}

export default function AdminGuard({ children, session }: AdminGuardProps) {
  const router = useRouter();
  const { data: clientSession, status } = useSession();

  useEffect(() => {
    if (status === 'unauthenticated' || (clientSession?.user?.role !== 'admin' && session?.user?.role !== 'admin')) {
      router.push('/');
    }
  }, [status, clientSession, session, router]);

  if (status === 'loading') {
    return <div>Loading...</div>;
  }

  if ((status === 'authenticated' && clientSession?.user?.role === 'admin') || session?.user?.role === 'admin') {
    return <>{children}</>;
  }

  return null;
} 