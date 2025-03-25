import React from 'react';
import { Metadata } from 'next';
import { getServerSession } from 'next-auth';
import { authOptions } from '../lib/auth/options';
import AdminPageContent from '@/components/features/admin/AdminPageContent';

export const metadata: Metadata = {
  title: 'Admin Dashboard - CernoID Security',
  description: 'Administrative controls for CernoID Security System',
};

export default async function AdminPage() {
  const session = await getServerSession(authOptions);
  return <AdminPageContent session={session} />;
} 