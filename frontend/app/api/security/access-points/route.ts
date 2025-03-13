import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { prisma } from '@/lib/prisma';
import { 
  withAuth, 
  withAdminAuth,
  parseQueryParams, 
  buildPaginationResponse,
  PaginationSchema,
  type ApiResponse
} from '@/lib/api-utils';

const AccessPointSchema = z.object({
  name: z.string(),
  type: z.string(),
  location: z.string(),
  status: z.enum(["active", "inactive", "maintenance"]),
  zoneId: z.string(),
  settings: z.any().optional(),
});

const QuerySchema = PaginationSchema.extend({
  name: z.string().optional(),
  type: z.string().optional(),
  location: z.string().optional(),
  status: z.enum(["active", "inactive", "maintenance"]).optional(),
  zoneId: z.string().optional(),
  zone: z.string().optional(),
});

export async function GET(request: NextRequest) {
  return withAuth(request, async (session) => {
    const query = parseQueryParams(request, QuerySchema);
    const { page, limit } = query;
    const skip = (page - 1) * limit;

    const where = {
      ...(query.name && { name: { contains: query.name } }),
      ...(query.type && { type: query.type }),
      ...(query.location && { location: query.location }),
      ...(query.status && { status: query.status }),
      ...(query.zoneId && { zoneId: query.zoneId }),
      ...(query.zone && { zoneId: query.zone }),
    };

    const [total, accessPoints] = await Promise.all([
      prisma.accessPoint.count({ where }),
      prisma.accessPoint.findMany({
        where,
        take: limit,
        skip,
        orderBy: { createdAt: 'desc' },
        include: {
          zone: {
            select: {
              id: true,
              name: true,
              level: true,
            },
          },
        },
      }),
    ]);

    return NextResponse.json({
      success: true,
      data: buildPaginationResponse(accessPoints, total, query)
    }, { status: 200 });
  });
}

export async function POST(request: NextRequest) {
  return withAuth(request, async (session) => {
    const body = await request.json();
    const data = AccessPointSchema.parse(body);

    const existingAccessPoint = await prisma.accessPoint.findFirst({
      where: {
        name: data.name,
        zoneId: data.zoneId,
      },
    });

    if (existingAccessPoint) {
      return NextResponse.json({
        success: false,
        error: 'Access point already exists'
      }, { status: 409 });
    }

    try {
      const accessPoint = await prisma.accessPoint.create({
        data: {
          ...data,
          createdBy: session.id,
          updatedBy: session.id,
        },
      });

      return NextResponse.json({
        success: true,
        data: accessPoint
      }, { status: 201 });
    } catch (error) {
      console.error('Failed to create access point:', error);
      return NextResponse.json({
        success: false,
        error: "Failed to create access point"
      }, { status: 500 });
    }
  });
}

export async function PUT(request: NextRequest) {
  return withAuth(request, async (session) => {
    const body = await request.json();
    const { id, ...data } = body;

    if (!id) {
      return NextResponse.json({
        success: false,
        error: 'Access point ID is required'
      }, { status: 400 });
    }

    const validatedData = AccessPointSchema.parse(data);

    try {
      const accessPoint = await prisma.accessPoint.update({
        where: { id },
        data: {
          ...validatedData,
          updatedBy: session.id,
        },
      });

      return NextResponse.json({
        success: true,
        data: accessPoint
      }, { status: 200 });
    } catch (error) {
      return NextResponse.json({
        success: false,
        error: 'Failed to update access point'
      }, { status: 500 });
    }
  });
}

export async function DELETE(request: NextRequest) {
  return withAuth(request, async () => {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id) {
      return NextResponse.json({
        success: false,
        error: 'Access point ID is required'
      }, { status: 400 });
    }

    try {
      await prisma.accessPoint.delete({
        where: { id },
      });

      return NextResponse.json({
        success: true,
        message: 'Access point deleted successfully'
      }, { status: 200 });
    } catch (error) {
      return NextResponse.json({
        success: false,
        error: 'Failed to delete access point'
      }, { status: 500 });
    }
  });
} 