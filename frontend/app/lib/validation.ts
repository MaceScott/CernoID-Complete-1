import { z } from 'zod';

export const UserSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  role: z.enum(['user', 'admin']).default('user'),
});

export const CameraSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  url: z.string().url('Invalid camera URL'),
  location: z.string().optional(),
  status: z.enum(['online', 'offline']).default('offline'),
});

export const RecognitionSchema = z.object({
  userId: z.string().cuid('Invalid user ID'),
  cameraId: z.string().cuid('Invalid camera ID'),
  confidence: z.number().min(0).max(1),
  metadata: z.record(z.unknown()).optional(),
});

export const PermissionSchema = z.object({
  role: z.string().min(1, 'Role is required'),
  resource: z.string().min(1, 'Resource is required'),
  action: z.enum(['create', 'read', 'update', 'delete']),
  location: z.string().optional(),
});

export const LoginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
});

export const RegisterSchema = UserSchema.pick({
  name: true,
  email: true,
  password: true,
}); 