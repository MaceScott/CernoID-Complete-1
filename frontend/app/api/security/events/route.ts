import { NextResponse } from 'next/server'
import { z } from 'zod'
import { prisma } from '../../../lib/prisma'
import type { NextRequest } from 'next/server'
import { 
  withAuth, 
  parseQueryParams, 
  buildPaginationResponse,
  PaginationSchema,
  type ApiResponse 
} from '../../../lib/api-utils'

const QuerySchema = PaginationSchema.extend({
  startDate: z.string().optional(),
  endDate: z.string().optional(),
  sourceType: z.string().optional(),
  severity: z.enum(['low', 'medium', 'high']).optional(),
  status: z.enum(['open', 'closed', 'in_progress']).optional(),
  assignedTo: z.string().optional(),
});

export async function GET(request: NextRequest) {
  return withAuth(request, async (user) => {
    const query = parseQueryParams(request.nextUrl.searchParams, QuerySchema)
    const skip = (query.page - 1) * query.limit

    const where = {
      ...(query.startDate && {
        createdAt: { gte: new Date(query.startDate) },
      }),
      ...(query.endDate && {
        createdAt: { 
          ...((query.startDate && { gte: new Date(query.startDate) }) || {}),
          lte: new Date(query.endDate),
        },
      }),
      ...(query.sourceType && { sourceType: query.sourceType }),
      ...(query.severity && { severity: query.severity }),
      ...(query.status && { status: query.status }),
      ...(query.assignedTo && { assignedTo: query.assignedTo }),
    }

    const [total, alerts] = await Promise.all([
      prisma.alert.count({ where }),
      prisma.alert.findMany({
        where,
        orderBy: { createdAt: 'desc' },
        take: query.limit,
        skip,
        include: {
          creator: true,
          assignedUser: true,
          camera: true,
          accessPoint: true,
        },
      }),
    ])

    const response = buildPaginationResponse(alerts, total, query)
    return NextResponse.json<ApiResponse<typeof response>>({ 
      success: true, 
      data: response 
    }, { status: 200 })
  })
}

export async function POST(request: NextRequest) {
  return withAuth(request, async (user) => {
    const data = await request.json()
    
    const alert = await prisma.alert.create({
      data: {
        ...data,
        createdBy: user.id,
        updatedBy: user.id,
      },
      include: {
        creator: true,
        assignedUser: true,
        camera: true,
        accessPoint: true,
      },
    })

    return NextResponse.json<ApiResponse<typeof alert>>({ 
      success: true, 
      data: alert 
    }, { status: 201 })
  })
} 