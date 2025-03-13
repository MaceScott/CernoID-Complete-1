'use client';

import React from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Box,
} from '@mui/material';
import { useOptimizedQuery } from '@/hooks/useOptimizedQuery';

interface AuditLogEntry {
  id: string;
  timestamp: string;
  action: string;
  userId: string;
  details: string;
  ipAddress: string;
}

export function AuditLog() {
  const { data: logs, isLoading, error } = useOptimizedQuery<AuditLogEntry[]>({
    key: 'audit-logs',
    fetchFn: async () => {
      const response = await fetch('/api/admin/audit-logs');
      if (!response.ok) throw new Error('Failed to fetch audit logs');
      return response.json();
    },
    staleTime: 60000, // 1 minute
  });

  if (isLoading) {
    return <Typography>Loading audit logs...</Typography>;
  }

  if (error) {
    return <Typography color="error">Error loading audit logs: {error.message}</Typography>;
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        System Audit Log
      </Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Timestamp</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>User ID</TableCell>
              <TableCell>Details</TableCell>
              <TableCell>IP Address</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {logs?.map((log) => (
              <TableRow key={log.id}>
                <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                <TableCell>{log.action}</TableCell>
                <TableCell>{log.userId}</TableCell>
                <TableCell>{log.details}</TableCell>
                <TableCell>{log.ipAddress}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
} 