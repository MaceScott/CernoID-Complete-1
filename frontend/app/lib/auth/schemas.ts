import { z } from 'zod';

export const SecurityEventSchema = z.object({
  id: z.string().optional(),
  type: z.string(),
  severity: z.enum(['low', 'medium', 'high']),
  message: z.string(),
  timestamp: z.string().datetime().optional(),
  cameraId: z.string().optional(),
  zoneId: z.string().optional(),
  userId: z.string().optional(),
  metadata: z.record(z.unknown()).optional(),
});

export const PermissionSchema = z.object({
  id: z.string().optional(),
  role: z.string(),
  resource: z.string(),
  action: z.string(),
  location: z.string().optional(),
});

export const SecurityZoneSchema = z.object({
  id: z.string().optional(),
  name: z.string(),
  description: z.string().optional(),
  level: z.number().min(0).max(10),
  parent_id: z.string().optional(),
  metadata: z.record(z.unknown()).optional(),
  cameras: z.array(z.string()).optional(),
  allowedRoles: z.array(z.string()).optional(),
  allowedUsers: z.array(z.string()).optional(),
  schedules: z.array(z.object({
    days: z.array(z.number().min(0).max(6)),
    start: z.string(),
    end: z.string(),
  })).optional(),
}); 