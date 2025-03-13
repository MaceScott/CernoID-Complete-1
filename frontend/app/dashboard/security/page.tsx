'use client';

import { Container } from '@mui/material';
import { SecurityDashboard } from '@/admin/components/SecurityDashboard';
import { useAuth } from '@/hooks/useAuth';

export default function SecurityPage() {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <Container maxWidth="lg">
      <SecurityDashboard />
    </Container>
  );
} 