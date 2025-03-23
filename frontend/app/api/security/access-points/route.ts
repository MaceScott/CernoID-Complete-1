import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { prisma } from '@/lib/prisma';
import { 
  withAuth, 
  withAdminAuth,
  parseQueryParams, 
  buildPaginationResponse,
  PaginationSchema,
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

async function handleGET(request: NextRequest): Promise<Response> {
  const query = parseQueryParams(request, QuerySchema);
  const { page, pageSize } = query;
  const skip = (page - 1) * pageSize;

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
      take: pageSize,
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
    data: buildPaginationResponse(accessPoints, total, page, pageSize)
  }, { status: 200 });
}

async function handlePOST(request: NextRequest): Promise<Response> {
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
        createdBy: request.headers.get('x-user-id') || '',
        updatedBy: request.headers.get('x-user-id') || '',
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
}

async function handlePUT(request: NextRequest): Promise<Response> {
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
        updatedBy: request.headers.get('x-user-id') || '',
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
}

async function handleDELETE(request: NextRequest): Promise<Response> {
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
}

export const GET = withAuth(handleGET);
export const POST = withAuth(handlePOST);
export const PUT = withAuth(handlePUT);
export const DELETE = withAuth(handleDELETE); 