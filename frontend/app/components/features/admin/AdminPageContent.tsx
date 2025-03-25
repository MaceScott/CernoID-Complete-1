'use client';

import React from 'react';
import { AdminDashboard } from '@/components/features/admin/AdminDashboard';
import { Box } from '@mui/material';
import AuthGuard from '@/components/Auth/AuthGuard';
import AdminGuard from '@/components/Auth/AdminGuard';

interface AdminPageContentProps {
  session?: any;
}

export default function AdminPageContent({ session }: AdminPageContentProps) {
  return (
    <AuthGuard>
      <AdminGuard session={session}>
        <Box sx={{ height: '100vh', overflow: 'hidden' }}>
          <AdminDashboard />
        </Box>
      </AdminGuard>
    </AuthGuard>
  );
} 