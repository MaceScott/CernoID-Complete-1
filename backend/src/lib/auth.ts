import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth/options";
import { prisma } from "@/lib/prisma";
import { cache } from "react";
import { z } from "zod";
import type { Prisma } from "@prisma/client";

export type AuthUser = {
  id: string;
  email: string;
  name: string | null;
  isAdmin: boolean;
  accessLevel: number;
  allowedZones: string[];
  role: string;
  status: string;
  lastLogin: Date | null;
  lastAccess: Date | null;
  accessHistory: Prisma.JsonValue | null;
  preferences: Prisma.JsonValue | null;
};

// Cache the current session to avoid multiple DB calls
export const getSession = cache(async () => {
  return await getServerSession(authOptions);
});

// Get the current authenticated user with security details
export async function getCurrentUser(): Promise<AuthUser | null> {
  const session = await getSession();
  
  if (!session?.user?.email) {
    return null;
  }

  const user = await prisma.user.findUnique({
    where: { email: session.user.email },
    select: {
      id: true,
      email: true,
      name: true,
      isAdmin: true,
      accessLevel: true,
      allowedZones: true,
      role: true,
      status: true,
      lastLogin: true,
      lastAccess: true,
      accessHistory: true,
      preferences: true,
    },
  });

  if (user) {
    // Update last access time
    await prisma.user.update({
      where: { id: user.id },
      data: { lastAccess: new Date() },
    });
  }

  return user;
}

// Check if user has required permission
export async function checkPermission(
  userId: string,
  resource: string,
  action: string,
  location?: string
): Promise<boolean> {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { isAdmin: true, role: true },
  });

  if (!user) {
    return false;
  }

  if (user.isAdmin) {
    return true;
  }

  const permission = await prisma.permission.findFirst({
    where: {
      role: user.role,
      resource,
      action,
      ...(location && { location }),
    },
  });

  return !!permission;
}

// Validate zone access for a user
export async function checkZoneAccess(
  userId: string,
  zoneId: string
): Promise<boolean> {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { 
      isAdmin: true, 
      allowedZones: true, 
      accessLevel: true,
      status: true 
    },
  });

  if (!user || user.status !== 'active') {
    return false;
  }

  if (user.isAdmin) {
    return true;
  }

  const zone = await prisma.securityZone.findUnique({
    where: { id: zoneId },
    select: { 
      level: true,
      requiredAccess: true,
    },
  });

  if (!zone) {
    return false;
  }

  return !!(
    user.allowedZones.includes(zoneId) &&
    user.accessLevel >= zone.level &&
    zone.requiredAccess.every((access: string) => user.allowedZones.includes(access))
  );
}

// Update user's access history
export async function updateAccessHistory(
  userId: string,
  action: string,
  details: Record<string, unknown>
): Promise<void> {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { accessHistory: true },
  });

  const history = user?.accessHistory as Record<string, unknown[]> || {};
  const timestamp = new Date().toISOString();

  if (!history[action]) {
    history[action] = [];
  }

  history[action].push({
    timestamp,
    ...details,
  });

  // Keep only last 100 entries per action
  if (history[action].length > 100) {
    history[action] = history[action].slice(-100);
  }

  await prisma.user.update({
    where: { id: userId },
    data: { accessHistory: history as Prisma.InputJsonValue },
  });
}

// Schema for validating security event data
export const SecurityEventSchema = z.object({
  type: z.string(),
  location: z.string(),
  personId: z.string().optional(),
  details: z.string(),
  severity: z.enum(["low", "medium", "high"]),
  metadata: z.any().optional(),
  createdBy: z.string(),
}) satisfies z.ZodType<Prisma.SecurityEventUncheckedCreateInput>;

// Schema for validating permission data
export const PermissionSchema = z.object({
  role: z.string(),
  resource: z.string(),
  action: z.enum(["read", "write", "admin"]),
  location: z.string().optional(),
  conditions: z.any().optional(),
  createdBy: z.string(),
  updatedBy: z.string(),
}) satisfies z.ZodType<Prisma.PermissionUncheckedCreateInput>;

// Schema for validating security zone data
export const SecurityZoneSchema = z.object({
  name: z.string(),
  level: z.number().int().min(0),
  requiredAccess: z.array(z.string()),
  locations: z.array(z.string()),
  description: z.string().optional(),
  parentZoneId: z.string().optional(),
  settings: z.any().optional(),
  createdBy: z.string(),
  updatedBy: z.string(),
}) satisfies z.ZodType<Prisma.SecurityZoneUncheckedCreateInput>;

// Schema for validating camera data
export const CameraSchema = z.object({
  name: z.string(),
  type: z.string(),
  location: z.string(),
  status: z.enum(["active", "inactive", "maintenance"]),
  zoneId: z.string(),
  settings: z.any().optional(),
  createdBy: z.string(),
  updatedBy: z.string(),
}) satisfies z.ZodType<Prisma.CameraUncheckedCreateInput>;

// Schema for validating access point data
export const AccessPointSchema = z.object({
  name: z.string(),
  type: z.string(),
  location: z.string(),
  status: z.enum(["active", "inactive", "maintenance"]),
  zoneId: z.string(),
  settings: z.any().optional(),
  createdBy: z.string(),
  updatedBy: z.string(),
}) satisfies z.ZodType<Prisma.AccessPointUncheckedCreateInput>;

// Schema for validating alert data
export const AlertSchema = z.object({
  type: z.string(),
  severity: z.string(),
  message: z.string(),
  status: z.enum(["open", "resolved", "dismissed"]).default("open"),
  cameraId: z.string().optional(),
  resolvedAt: z.date().optional(),
  resolvedBy: z.string().optional(),
  userId: z.string(),
}) satisfies z.ZodType<Prisma.AlertUncheckedCreateInput>;

// Log security event with enhanced tracking
export async function logSecurityEvent(
  data: z.infer<typeof SecurityEventSchema>,
  userId: string
): Promise<void> {
  const event = await prisma.securityEvent.create({
    data: {
      ...data,
      createdBy: userId,
    },
  });

  // Update access history for the user
  await updateAccessHistory(userId, 'security_event', {
    eventId: event.id,
    type: event.type,
  });
} 