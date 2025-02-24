import { Prisma } from '@prisma/client'

const prisma = new Prisma()

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
          createdAt: true,
          lastLogin: true,
        },
      })
    },
    // Add more user operations...
  },
  cameras: {
    findMany: async () => {
      return prisma.camera.findMany({
        include: {
          alerts: true,
          settings: true,
        },
      })
    },
    // Add more camera operations...
  },
  alerts: {
    findMany: async () => {
      return prisma.alert.findMany({
        include: {
          camera: true,
        },
        orderBy: {
          timestamp: 'desc',
        },
      })
    },
    // Add more alert operations...
  },
} 