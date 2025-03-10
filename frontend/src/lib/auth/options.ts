import { NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { prisma } from '../prisma';
import { compare } from 'bcryptjs';

declare module 'next-auth' {
  interface Session {
    user: {
      id: string;
      username: string;
      email: string;
      role: string;
      permissions: string[];
      firstName?: string;
      lastName?: string;
      phone?: string;
      active: boolean;
      lastLogin?: Date;
    }
  }

  interface JWT {
    role?: string;
    permissions?: string[];
    active?: boolean;
    username?: string;
  }

  interface User {
    id: string;
    username: string;
    email: string;
    role: string;
    permissions: string[];
    firstName?: string;
    lastName?: string;
    phone?: string;
    active: boolean;
    lastLogin?: Date;
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
          role: user.role,
          permissions: user.permissions,
          firstName: user.first_name,
          lastName: user.last_name,
          phone: user.phone,
          active: user.active,
          lastLogin: user.last_login
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