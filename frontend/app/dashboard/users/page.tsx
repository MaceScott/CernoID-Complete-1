'use client';

import { Container } from '@mui/material';
import { UserManagement } from '@/components/features/users';
import { useAuth } from '@/hooks/useAuth';

export default function UsersPage() {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <Container maxWidth="lg">
      <UserManagement />
    </Container>
  );
} 