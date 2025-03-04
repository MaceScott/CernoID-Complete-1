import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

export const db = {
  users: {
    findMany: async () => {
      return prisma.user.findMany({
        select: {
          id: true,
          name: true,
          email: true,
          role: true,
          status: true,
          isAdmin: true,
          accessLevel: true,
          allowedZones: true,
          lastLogin: true,
          lastAccess: true,
          createdAt: true,
          updatedAt: true,
        },
      })
    },
    // Add more user operations...
  },
  securityEvents: {
    findMany: async () => {
      return prisma.securityEvent.findMany({
        include: {
          person: {
            select: {
              id: true,
              name: true,
              email: true,
            },
          },
        },
        orderBy: {
          timestamp: 'desc',
        },
      })
    },
  },
  permissions: {
    findMany: async () => {
      return prisma.permission.findMany({
        orderBy: {
          role: 'asc',
        },
      })
    },
  },
  securityZones: {
    findMany: async () => {
      return prisma.securityZone.findMany({
        include: {
          cameras: {
            select: {
              id: true,
              name: true,
              type: true,
              status: true,
            },
          },
          accessPoints: {
            select: {
              id: true,
              name: true,
              type: true,
              status: true,
            },
          },
          children: {
            select: {
              id: true,
              name: true,
              level: true,
            },
          },
          parent: {
            select: {
              id: true,
              name: true,
              level: true,
            },
          },
        },
        orderBy: {
          name: 'asc',
        },
      })
    },
  },
  cameras: {
    findMany: async () => {
      return prisma.camera.findMany({
        include: {
          zone: {
            select: {
              id: true,
              name: true,
              level: true,
            },
          },
          alerts: {
            where: { status: 'open' },
            select: {
              id: true,
              type: true,
              severity: true,
              message: true,
              createdAt: true,
            },
            take: 5,
            orderBy: { createdAt: 'desc' },
          },
        },
        orderBy: {
          name: 'asc',
        },
      })
    },
    // Add more camera operations...
  },
  accessPoints: {
    findMany: async () => {
      return prisma.accessPoint.findMany({
        include: {
          zone: {
            select: {
              id: true,
              name: true,
              level: true,
            },
          },
        },
        orderBy: {
          name: 'asc',
        },
      })
    },
  },
  alerts: {
    findMany: async () => {
      return prisma.alert.findMany({
        include: {
          camera: {
            select: {
              id: true,
              name: true,
              type: true,
              location: true,
              status: true,
            },
          },
          user: {
            select: {
              id: true,
              name: true,
              email: true,
            },
          },
        },
        orderBy: {
          createdAt: 'desc',
        },
      })
    },
    // Add more alert operations...
  },
} 