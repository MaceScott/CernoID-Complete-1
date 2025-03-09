import { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

export async function getAuthToken(req: NextRequest) {
  return await getToken({ req });
}

export async function isAuthenticated(req: NextRequest) {
  const token = await getAuthToken(req);
  return !!token;
}

export async function hasRole(req: NextRequest, role: string) {
  const token = await getAuthToken(req);
  return token?.role === role;
}

export async function isAdmin(req: NextRequest) {
  const token = await getAuthToken(req);
  return token?.isAdmin === true;
}

export async function hasAccessLevel(req: NextRequest, level: string) {
  const token = await getAuthToken(req);
  return token?.accessLevel === level;
}

export async function hasZoneAccess(req: NextRequest, zoneId: string) {
  const token = await getAuthToken(req);
  const allowedZones = token?.allowedZones as string[] | undefined;
  return allowedZones?.includes(zoneId) ?? false;
}

export async function getUserId(req: NextRequest) {
  const token = await getAuthToken(req);
  return token?.sub;
}

export async function getUsername(req: NextRequest) {
  const token = await getAuthToken(req);
  return token?.username;
}

export async function getUserRole(req: NextRequest) {
  const token = await getAuthToken(req);
  return token?.role;
}

export async function getUserAccessLevel(req: NextRequest) {
  const token = await getAuthToken(req);
  return token?.accessLevel;
}

export async function getUserAllowedZones(req: NextRequest) {
  const token = await getAuthToken(req);
  return (token?.allowedZones as string[] | undefined) || [];
} 