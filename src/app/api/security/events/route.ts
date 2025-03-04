import { NextResponse } from 'next/server'
import { z } from 'zod'
import { prisma } from '@/lib/prisma'
import { SecurityEventSchema } from '@/lib/auth'
import { 
  withAuth, 
  parseQueryParams, 
  buildPaginationResponse,
  PaginationSchema 
} from '@/lib/api-utils'

const QuerySchema = PaginationSchema.extend({
  startDate: z.string().optional(),
  endDate: z.string().optional(),
  type: z.string().optional(),
  location: z.string().optional(),
  severity: z.enum(['low', 'medium', 'high']).optional(),
  personId: z.string().optional(),
})

export async function GET(request: Request) {
  return withAuth(async () => {
    const { searchParams } = new URL(request.url)
    const query = parseQueryParams(searchParams, QuerySchema)

    const where = {
      ...(query.startDate && {
        timestamp: { gte: new Date(query.startDate) },
      }),
      ...(query.endDate && {
        timestamp: { 
          ...((query.startDate && { gte: new Date(query.startDate) }) || {}),
          lte: new Date(query.endDate),
        },
      }),
      ...(query.type && { type: query.type }),
      ...(query.location && { location: query.location }),
      ...(query.severity && { severity: query.severity }),
      ...(query.personId && { personId: query.personId }),
    }

    const [total, events] = await Promise.all([
      prisma.securityEvent.count({ where }),
      prisma.securityEvent.findMany({
        where,
        orderBy: { timestamp: 'desc' },
        take: query.limit || 10,
        skip: query.offset || 0,
        include: {
          person: {
            select: {
              id: true,
              name: true,
              email: true,
            },
          },
        },
      }),
    ])

    return buildPaginationResponse(
      events,
      total,
      query.limit || 10,
      query.offset || 0
    )
  })
}

export async function POST(request: Request) {
  return withAuth(async (user) => {
    if (!user) throw new Error("User is required")

    const body = await request.json()
    const data = SecurityEventSchema.parse(body)

    const event = await prisma.securityEvent.create({
      data: {
        ...data,
        createdBy: user.id,
      },
      include: {
        person: {
          select: {
            id: true,
            name: true,
            email: true,
          },
        },
      },
    })

    return NextResponse.json(event, { status: 201 })
  })
} 