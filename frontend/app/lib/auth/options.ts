import { AuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';
import { JWT } from 'next-auth/jwt';
import { Session } from 'next-auth';

const prisma = new PrismaClient();

export const authOptions: AuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error('Please enter an email and password');
        }

        const user = await prisma.user.findUnique({
          where: {
            email: credentials.email,
          },
        });

        if (!user) {
          throw new Error('No user found with this email');
        }

        const isPasswordValid = await bcrypt.compare(
          credentials.password,
          user.password || ''
        );

        if (!isPasswordValid) {
          throw new Error('Invalid password');
        }

        return {
          id: user.id,
          email: user.email,
          name: user.name,
          role: user.role,
          isAdmin: user.role === 'admin',
          accessLevel: 1,
          allowedZones: [],
          status: 'active',
          createdAt: user.createdAt,
          updatedAt: user.updatedAt,
          lastLogin: null,
        };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }: { token: JWT; user: any }) {
      if (user) {
        token.role = user.role;
        token.isAdmin = user.isAdmin;
        token.accessLevel = user.accessLevel;
        token.allowedZones = user.allowedZones;
      }
      return token;
    },
    async session({ session, token }: { session: Session; token: JWT }) {
      if (session?.user) {
        session.user.role = token.role as string;
        session.user.isAdmin = token.isAdmin as boolean;
        session.user.accessLevel = token.accessLevel as number;
        session.user.allowedZones = token.allowedZones as string[];
      }
      return session;
    },
  },
  pages: {
    signIn: '/auth/login',
  },
  session: {
    strategy: 'jwt' as const,
  },
}; 