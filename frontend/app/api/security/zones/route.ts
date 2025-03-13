import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { prisma } from '@/lib/prisma'
import { SecurityZoneSchema } from '@/lib/auth/schemas'
import { 
  withAuth, 
  parseQueryParams, 
  buildPaginationResponse,
  PaginationSchema,
  type ApiResponse
} from '@/lib/api-utils'

const QuerySchema = PaginationSchema.extend({
  level: z.number().int().min(0).optional(),
})

export async function GET(request: NextRequest) {
  return withAuth(request, async (session) => {
    const query = parseQueryParams(request.nextUrl.searchParams, QuerySchema)
    const { page, limit } = query
    const skip = (page - 1) * limit

    const where = {
      ...(query.level !== undefined && { level: query.level }),
    }

    const [total, zones] = await Promise.all([
      prisma.zone.count({ where }),
      prisma.zone.findMany({
        where,
        take: limit,
        skip,
        orderBy: { createdAt: 'desc' },
        include: {
          creator: true,
          accessPoints: true,
        },
      }),
    ])

    const response = buildPaginationResponse(zones, total, query)
    return NextResponse.json<ApiResponse<typeof response>>({
      success: true,
      data: response,
    }, { status: 200 })
  })
}

export async function POST(request: NextRequest) {
  return withAuth(request, async (session) => {
    const body = await request.json()
    const data = SecurityZoneSchema.parse(body)

    const existingZone = await prisma.zone.findFirst({
      where: {
        name: data.name,
      },
    })

    if (existingZone) {
      return NextResponse.json<ApiResponse<null>>({
        success: false,
        error: 'Zone already exists',
      }, { status: 409 })
    }

    const zone = await prisma.zone.create({
      data: {
        name: data.name,
        description: data.description,
        level: data.level,
        createdBy: session.user.id,
        updatedBy: session.user.id,
      },
      include: {
        creator: true,
        accessPoints: true,
      },
    })

    return NextResponse.json<ApiResponse<typeof zone>>({
      success: true,
      data: zone,
    }, { status: 201 })
  })
}

export async function PUT(request: NextRequest) {
  return withAuth(request, async (session) => {
    const body = await request.json()
    const { id, ...data } = body

    if (!id) {
      return NextResponse.json<ApiResponse<null>>({
        success: false,
        error: 'Zone ID is required'
      }, { status: 400 })
    }

    const validatedData = SecurityZoneSchema.parse(data)

    const zone = await prisma.zone.update({
      where: { id },
      data: {
        name: validatedData.name,
        description: validatedData.description,
        level: validatedData.level,
        updatedBy: session.user.id,
      },
      include: {
        creator: true,
        accessPoints: true,
      },
    })

    return NextResponse.json<ApiResponse<typeof zone>>({
      success: true,
      data: zone
    }, { status: 200 })
  })
}

export async function DELETE(request: NextRequest) {
  return withAuth(request, async () => {
    const { searchParams } = new URL(request.url)
    const id = searchParams.get('id')

    if (!id) {
      return NextResponse.json<ApiResponse<null>>({
        success: false,
        error: 'Zone ID is required'
      }, { status: 400 })
    }

    const zone = await prisma.zone.findUnique({
      where: { id },
      include: {
        accessPoints: true,
      },
    })

    if (!zone) {
      return NextResponse.json<ApiResponse<null>>({
        success: false,
        error: 'Zone not found'
      }, { status: 404 })
    }

    if (zone.accessPoints.length > 0) {
      return NextResponse.json<ApiResponse<null>>({
        success: false,
        error: 'Cannot delete zone with associated access points'
      }, { status: 400 })
    }

    await prisma.zone.delete({
      where: { id },
    })

    return NextResponse.json<ApiResponse<null>>({
      success: true,
      data: null
    }, { status: 200 })
  })
} 