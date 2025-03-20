import NextAuth, { DefaultSession } from "next-auth";
import { Prisma } from "@prisma/client";

declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      isAdmin: boolean;
      accessLevel: number;
      allowedZones: string[];
    } & DefaultSession["user"];
  }

  interface User {
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
  }
} 