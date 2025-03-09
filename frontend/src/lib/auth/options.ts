import { NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { prisma } from '../prisma';
import { compare } from 'bcryptjs';
import { User } from '@/types';

declare module 'next-auth' {
  interface Session {
    user: User;
  }
}

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        const user = await prisma.user.findUnique({
          where: { email: credentials.email }
        });

        if (!user) {
          return null;
        }

        const isValid = await compare(credentials.password, user.password);

        if (!isValid) {
          return null;
        }

        return {
          id: user.id,
          username: user.username,
          email: user.email,
          name: user.name,
          role: user.role,
          status: user.status as 'active' | 'inactive' | 'suspended',
          isAdmin: user.isAdmin,
          accessLevel: user.accessLevel,
          allowedZones: user.allowedZones,
          lastLogin: user.lastLogin,
          createdAt: user.createdAt,
          updatedAt: user.updatedAt
        };
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
          status: token.status as 'active' | 'inactive' | 'suspended',
          isAdmin: token.isAdmin as boolean,
          accessLevel: token.accessLevel as string,
          allowedZones: token.allowedZones as string[],
          username: token.username as string
        }
      };
    },
    async jwt({ token, user }) {
      if (user) {
        token.role = user.role;
        token.status = user.status;
        token.isAdmin = user.isAdmin;
        token.accessLevel = user.accessLevel;
        token.allowedZones = user.allowedZones;
        token.username = user.username;
      }
      return token;
    }
  }
}; 