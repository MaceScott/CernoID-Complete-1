import { NextAuthOptions, DefaultSession, DefaultUser } from 'next-auth';
import { JWT } from 'next-auth/jwt';
import CredentialsProvider from 'next-auth/providers/credentials';
import { prisma } from '../prisma';
import { compare } from 'bcryptjs';
import type { Prisma } from '@prisma/client';

interface CustomUser extends DefaultUser {
  username: string;
  role: string;
  permissions: string[];
  firstName: string | null;
  lastName: string | null;
  phone: string | null;
  active: boolean;
  lastLogin: Date | null;
}

declare module 'next-auth' {
  interface Session extends DefaultSession {
    user: CustomUser;
  }

  interface JWT {
    role?: string;
    permissions?: string[];
    active?: boolean;
    username?: string;
  }

  interface User extends CustomUser {}
}

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' }
      },
      async authorize(credentials, req) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        const user = await prisma.user.findUnique({
          where: { email: credentials.email },
          include: {
            permissions: true
          }
        });

        if (!user || !user.email) {
          return null;
        }

        const isValid = await compare(credentials.password, user.password || '');

        if (!isValid) {
          return null;
        }

        // Ensure we only return users with valid email addresses and required fields
        const [firstName, lastName] = (user.name || '').split(' ');
        const permissions = user.permissions.map((p: { resource: string; action: string }) => `${p.resource}:${p.action}`);

        return {
          id: user.id,
          username: user.name || 'Anonymous',
          name: user.name || 'Anonymous',
          email: user.email,
          role: user.role,
          permissions,
          firstName: firstName || null,
          lastName: lastName || null,
          phone: null,
          active: true,
          lastLogin: user.updatedAt,
          image: user.image,
          emailVerified: user.emailVerified
        } as CustomUser;
      }
    })
  ],
  session: {
    strategy: 'jwt'
  },
  pages: {
    signIn: '/login',
    error: '/login'
  },
  callbacks: {
    async session({ session, token }) {
      return {
        ...session,
        user: {
          ...session.user,
          id: token.sub,
          role: token.role as string,
          permissions: token.permissions as string[],
          active: token.active as boolean,
          username: token.username as string
        }
      };
    },
    async jwt({ token, user }) {
      if (user) {
        token.role = user.role;
        token.permissions = user.permissions;
        token.active = user.active;
        token.username = user.username;
      }
      return token;
    }
  }
}; 