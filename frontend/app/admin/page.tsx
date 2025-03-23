// Remove or comment out the 'use client' directive if it exists

import React from 'react';
import { AdminDashboard } from '@/components/features/admin/AdminDashboard';
import { Box } from '@mui/material';
import { Metadata } from 'next';
import AuthGuard from '@/components/Auth/AuthGuard';
import AdminGuard from '@/components/Auth/AdminGuard';

export const metadata: Metadata = {
  title: 'Admin Dashboard - CernoID Security',
  description: 'Administrative controls for CernoID Security System',
};

export default function AdminPage() {
  return (
    <AuthGuard>
      <AdminGuard>
        <Box sx={{ height: '100vh', overflow: 'hidden' }}>
          <AdminDashboard />
        </Box>
      </AdminGuard>
    </AuthGuard>
  );
} 