'use client';

import React, { useState } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Tabs,
  Tab,
  Divider,
  useTheme,
} from '@mui/material';
import { BaseFrame } from '@/desktop/BaseFrame';
import { UserManagement } from './UserManagement';
import { SystemSettings } from './SystemSettings';
import { SecuritySettings } from './SecuritySettings';
import { AuditLog } from './AuditLog';
import { motion } from 'framer-motion';

const MotionPaper = motion(Paper);
const MotionTypography = motion(Typography);

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <Box
      role="tabpanel"
      hidden={value !== index}
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
    >
      {value === index && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Box sx={{ py: 3 }}>
            {children}
          </Box>
        </motion.div>
      )}
    </Box>
  );
}

function a11yProps(index: number) {
  return {
    id: `admin-tab-${index}`,
    'aria-controls': `admin-tabpanel-${index}`,
  };
}

export function AdminDashboard() {
  const [tabValue, setTabValue] = useState(0);
  const theme = useTheme();

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <BaseFrame title="Admin Dashboard">
      <Container maxWidth="xl">
        <Box sx={{ mt: 4, mb: 6 }}>
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Typography
              variant="h3"
              component="h1"
              sx={{
                textAlign: 'center',
                fontWeight: 600,
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 1,
              }}
            >
              CernoID Security
            </Typography>
            <Typography
              variant="subtitle1"
              color="text.secondary"
              align="center"
              gutterBottom
            >
              Administrative Control Panel
            </Typography>
          </motion.div>
        </Box>

        <MotionPaper
          elevation={3}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="admin panel tabs"
            sx={{
              borderBottom: 1,
              borderColor: 'divider',
              '& .MuiTab-root': {
                minHeight: 64,
                fontSize: '1rem',
              },
            }}
          >
            <Tab 
              label="User Management" 
              {...a11yProps(0)}
              sx={{ fontWeight: 500 }}
            />
            <Tab 
              label="System Settings" 
              {...a11yProps(1)}
              sx={{ fontWeight: 500 }}
            />
            <Tab 
              label="Security Settings" 
              {...a11yProps(2)}
              sx={{ fontWeight: 500 }}
            />
            <Tab 
              label="Audit Log" 
              {...a11yProps(3)}
              sx={{ fontWeight: 500 }}
            />
          </Tabs>

          <Box sx={{ p: 3 }}>
            <TabPanel value={tabValue} index={0}>
              <UserManagement />
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              <SystemSettings />
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              <SecuritySettings />
            </TabPanel>

            <TabPanel value={tabValue} index={3}>
              <AuditLog />
            </TabPanel>
          </Box>
        </MotionPaper>
      </Container>
    </BaseFrame>
  );
} 