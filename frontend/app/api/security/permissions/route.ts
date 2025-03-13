import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { prisma } from '@/lib/prisma'
import { PermissionSchema } from '@/lib/auth/schemas'
import { 
  withAdminAuth, 
  parseQueryParams, 
  buildPaginationResponse,
  PaginationSchema,
  type ApiResponse
} from '@/lib/api-utils'

const QuerySchema = PaginationSchema.extend({
  role: z.string().optional(),
  resource: z.string().optional(),
  location: z.string().optional(),
})

export async function GET(request: NextRequest) {
  return withAdminAuth(request, async (session) => {
    const query = parseQueryParams(request, QuerySchema)
    const { page, limit } = query
    const skip = (page - 1) * limit

    const where = {
      ...(query.role && { role: query.role }),
      ...(query.resource && { resource: query.resource }),
      ...(query.location && { location: query.location }),
    }

    const [total, permissions] = await Promise.all([
      prisma.permission.count({ where }),
      prisma.permission.findMany({
        where,
        take: limit,
        skip,
        orderBy: { createdAt: 'desc' },
      }),
    ])

    return NextResponse.json({
      success: true,
      data: buildPaginationResponse(permissions, total, query)
    }, { status: 200 })
  })
}

export async function POST(request: NextRequest) {
  return withAdminAuth(request, async (session) => {
    const body = await request.json()
    const data = PermissionSchema.parse(body)

    const existingPermission = await prisma.permission.findFirst({
      where: {
        role: data.role,
        resource: data.resource,
        action: data.action,
        location: data.location,
      },
    })

    if (existingPermission) {
      return NextResponse.json<ApiResponse<null>>({
        success: false,
        error: 'Permission already exists',
      }, { status: 409 })
    }

    const permission = await prisma.permission.create({
      data: {
        ...data,
        createdBy: session.user.id,
        updatedBy: session.user.id,
      },
    })

    return NextResponse.json<ApiResponse<typeof permission>>({
      success: true,
      data: permission,
    }, { status: 201 })
  })
}

export async function PUT(request: NextRequest) {
  return withAdminAuth(request, async (session) => {
    const body = await request.json()
    const { id, ...data } = body

    if (!id) {
      return NextResponse.json({
        success: false,
        error: 'Permission ID is required'
      }, { status: 400 })
    }

    const validatedData = PermissionSchema.parse(data)

    try {
      const permission = await prisma.permission.update({
        where: { id },
        data: {
          ...validatedData,
          updatedBy: session.id,
        },
      })

      return NextResponse.json({
        success: true,
        data: permission
      }, { status: 200 })
    } catch (error) {
      return NextResponse.json({
        success: false,
        error: 'Failed to update permission'
      }, { status: 500 })
    }
  })
}

export async function DELETE(request: NextRequest) {
  return withAdminAuth(request, async () => {
    const { searchParams } = new URL(request.url)
    const id = searchParams.get('id')

    if (!id) {
      return NextResponse.json({
        success: false,
        error: 'Permission ID is required'
      }, { status: 400 })
    }

    try {
      await prisma.permission.delete({
        where: { id },
      })

      return NextResponse.json({
        success: true,
        message: 'Permission deleted successfully'
      }, { status: 200 })
    } catch (error) {
      return NextResponse.json({
        success: false,
        error: 'Failed to delete permission'
      }, { status: 500 })
    }
  })
} 