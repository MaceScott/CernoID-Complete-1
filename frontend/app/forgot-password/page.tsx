'use client';

import React, { useState } from 'react';
import { Container, Box, Paper, TextField, Button, Typography, CircularProgress } from '@mui/material';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ForgotPassword } from '@/components/Auth/ForgotPassword';
import { Card, CardContent } from '@mui/material';

export default function ForgotPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardContent>
          <Typography variant="h5" component="h1" className="mb-6 text-center">
            Reset Your Password
          </Typography>
          <Typography variant="body2" color="textSecondary" className="mb-4 text-center">
            Enter your email address and we&apos;ll send you instructions to reset your password.
          </Typography>
          <ForgotPassword />
        </CardContent>
      </Card>
    </div>
  );
} 