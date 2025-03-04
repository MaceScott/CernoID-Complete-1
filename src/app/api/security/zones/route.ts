import { NextResponse } from 'next/server'
import { z } from 'zod'
import { prisma } from '@/lib/prisma'
import { SecurityZoneSchema } from '@/lib/auth'
import { 
  withAdminAuth, 
  parseQueryParams, 
  buildPaginationResponse,
  PaginationSchema 
} from '@/lib/api-utils'

const QuerySchema = PaginationSchema.extend({
  name: z.string().optional(),
  level: z.string().transform(Number).optional(),
  location: z.string().optional(),
})

export async function GET(request: Request) {
  return withAdminAuth(async () => {
    const { searchParams } = new URL(request.url)
    const query = parseQueryParams(searchParams, QuerySchema)

    const where = {
      ...(query.name && { name: { contains: query.name } }),
      ...(query.level && { level: query.level }),
      ...(query.location && { locations: { has: query.location } }),
    }

    const [total, zones] = await Promise.all([
      prisma.securityZone.count({ where }),
      prisma.securityZone.findMany({
        where,
        take: query.limit || 10,
        skip: query.offset || 0,
        orderBy: { name: 'asc' },
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
      }),
    ])

    return buildPaginationResponse(
      zones,
      total,
      query.limit || 10,
      query.offset || 0
    )
  })
}

export async function POST(request: Request) {
  return withAdminAuth(async (user) => {
    if (!user) throw new Error("User is required")

    const body = await request.json()
    const data = SecurityZoneSchema.parse(body)

    const existingZone = await prisma.securityZone.findFirst({
      where: {
        name: data.name,
        locations: { hasEvery: data.locations },
      },
    })

    if (existingZone) {
      throw new Error('Security zone already exists for these locations')
    }

    const zone = await prisma.securityZone.create({
      data: {
        ...data,
        createdBy: user.id,
        updatedBy: user.id,
      },
      include: {
        cameras: true,
        accessPoints: true,
        children: true,
        parent: true,
      },
    })

    return NextResponse.json(zone, { status: 201 })
  })
}

export async function PUT(request: Request) {
  return withAdminAuth(async (user) => {
    if (!user) throw new Error("User is required")

    const body = await request.json()
    const { id, ...data } = body

    if (!id) {
      throw new Error('Security zone ID is required')
    }

    const validatedData = SecurityZoneSchema.parse(data)

    // Check for circular dependencies in parent-child relationships
    if (validatedData.parentZoneId) {
      const parentZone = await prisma.securityZone.findUnique({
        where: { id: validatedData.parentZoneId },
        include: {
          parent: true,
        },
      })

      if (parentZone?.id === id || parentZone?.parent?.id === id) {
        throw new Error('Circular parent-child relationship detected')
      }
    }

    const zone = await prisma.securityZone.update({
      where: { id },
      data: {
        ...validatedData,
        updatedBy: user.id,
      },
      include: {
        cameras: true,
        accessPoints: true,
        children: true,
        parent: true,
      },
    })

    return zone
  })
}

export async function DELETE(request: Request) {
  return withAdminAuth(async () => {
    const { searchParams } = new URL(request.url)
    const id = searchParams.get('id')

    if (!id) {
      throw new Error('Security zone ID is required')
    }

    // Check if zone has children
    const zone = await prisma.securityZone.findUnique({
      where: { id },
      include: {
        children: true,
        cameras: true,
        accessPoints: true,
      },
    })

    if (zone?.children.length) {
      throw new Error('Cannot delete zone with child zones')
    }

    if (zone?.cameras.length || zone?.accessPoints.length) {
      throw new Error('Cannot delete zone with associated devices')
    }

    await prisma.securityZone.delete({
      where: { id },
    })

    return { message: 'Security zone deleted successfully' }
  })
} 