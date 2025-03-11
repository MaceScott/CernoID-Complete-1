import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { prisma } from '../../../../lib/prisma'
import { PermissionSchema } from '../../../../lib/auth/schemas'
import { 
  withAdminAuth, 
  parseQueryParams, 
  buildPaginationResponse,
  PaginationSchema 
} from '../../../../lib/api-utils'
import { getServerSession } from 'next-auth/next'
import { authOptions } from '../../../../lib/auth/options'

const QuerySchema = PaginationSchema.extend({
  role: z.string().optional(),
  resource: z.string().optional(),
  location: z.string().optional(),
})

export async function GET(request: Request) {
  return withAdminAuth(async () => {
    const { searchParams } = new URL(request.url)
    const query = parseQueryParams(searchParams, QuerySchema)

    const where = {
      ...(query.role && { role: query.role }),
      ...(query.resource && { resource: query.resource }),
      ...(query.location && { location: query.location }),
    }

    const [total, permissions] = await Promise.all([
      prisma.permission.count({ where }),
      prisma.permission.findMany({
        where,
        take: query.limit || 10,
        skip: query.offset || 0,
        orderBy: { createdAt: 'desc' },
      }),
    ])

    return buildPaginationResponse(
      permissions,
      total,
      query.limit || 10,
      query.offset || 0
    )
  })
}

export async function POST(request: Request) {
  return withAdminAuth(async (user) => {
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
      throw new Error('Permission already exists')
    }

    try {
      const session = await getServerSession(authOptions)
      
      if (!session?.user) {
        return NextResponse.json(
          { error: "Unauthorized" },
          { status: 401 }
        )
      }

      const permission = await prisma.permission.create({
        data: {
          ...data,
          createdBy: session.user.id,
          updatedBy: session.user.id,
        },
      })

      return NextResponse.json(permission, { status: 201 })
    } catch (error) {
      console.error('Failed to create permission:', error)
      return NextResponse.json(
        { error: "Failed to create permission" },
        { status: 500 }
      )
    }
  })
}

export async function PUT(request: Request) {
  return withAdminAuth(async (user) => {
    const body = await request.json()
    const { id, ...data } = body

    if (!id) {
      throw new Error('Permission ID is required')
    }

    const validatedData = PermissionSchema.parse(data)

    const session = await getServerSession(authOptions)
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    try {
      const permission = await prisma.permission.update({
        where: { id },
        data: {
          ...validatedData,
          updatedBy: session.user.id,
        },
      })
      return NextResponse.json({ data: permission }, { status: 200 })
    } catch (error) {
      return NextResponse.json(
        { error: 'Failed to update permission' },
        { status: 500 }
      )
    }
  })
}

export async function DELETE(request: Request) {
  return withAdminAuth(async () => {
    const { searchParams } = new URL(request.url)
    const id = searchParams.get('id')

    if (!id) {
      throw new Error('Permission ID is required')
    }

    await prisma.permission.delete({
      where: { id },
    })

    return { message: 'Permission deleted successfully' }
  })
} 