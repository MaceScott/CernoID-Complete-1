import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { prisma } from '@/lib/prisma'
import { SecurityZoneSchema } from '@/lib/auth/schemas'
import { 
  withAuth, 
  parseQueryParams, 
  buildPaginationResponse,
  PaginationSchema,
} from '@/lib/api-utils'

const QuerySchema = PaginationSchema.extend({
  level: z.number().int().min(0).optional(),
})

async function handleGET(request: NextRequest): Promise<Response> {
  const query = parseQueryParams(request, QuerySchema);
  const { page, pageSize } = query;
  const skip = (page - 1) * pageSize;

  const where = {
    ...(query.level !== undefined && { level: query.level }),
  };

  const [total, zones] = await Promise.all([
    prisma.zone.count({ where }),
    prisma.zone.findMany({
      where,
      take: pageSize,
      skip,
      orderBy: { createdAt: 'desc' },
      include: {
        creator: true,
        accessPoints: true,
      },
    }),
  ]);

  return NextResponse.json({
    success: true,
    data: buildPaginationResponse(zones, total, page, pageSize),
  }, { status: 200 });
}

async function handlePOST(request: NextRequest): Promise<Response> {
  const body = await request.json();
  const data = SecurityZoneSchema.parse(body);

  const existingZone = await prisma.zone.findFirst({
    where: {
      name: data.name,
    },
  });

  if (existingZone) {
    return NextResponse.json({
      success: false,
      error: 'Zone already exists',
    }, { status: 409 });
  }

  const zone = await prisma.zone.create({
    data: {
      name: data.name,
      description: data.description,
      level: data.level,
      createdBy: request.headers.get('x-user-id') || '',
      updatedBy: request.headers.get('x-user-id') || '',
    },
    include: {
      creator: true,
      accessPoints: true,
    },
  });

  return NextResponse.json({
    success: true,
    data: zone,
  }, { status: 201 });
}

async function handlePUT(request: NextRequest): Promise<Response> {
  const body = await request.json();
  const { id, ...data } = body;

  if (!id) {
    return NextResponse.json({
      success: false,
      error: 'Zone ID is required'
    }, { status: 400 });
  }

  const validatedData = SecurityZoneSchema.parse(data);

  const zone = await prisma.zone.update({
    where: { id },
    data: {
      name: validatedData.name,
      description: validatedData.description,
      level: validatedData.level,
      updatedBy: request.headers.get('x-user-id') || '',
    },
    include: {
      creator: true,
      accessPoints: true,
    },
  });

  return NextResponse.json({
    success: true,
    data: zone
  }, { status: 200 });
}

async function handleDELETE(request: NextRequest): Promise<Response> {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get('id');

  if (!id) {
    return NextResponse.json({
      success: false,
      error: 'Zone ID is required'
    }, { status: 400 });
  }

  const zone = await prisma.zone.findUnique({
    where: { id },
    include: {
      accessPoints: true,
    },
  });

  if (!zone) {
    return NextResponse.json({
      success: false,
      error: 'Zone not found'
    }, { status: 404 });
  }

  if (zone.accessPoints.length > 0) {
    return NextResponse.json({
      success: false,
      error: 'Cannot delete zone with associated access points'
    }, { status: 400 });
  }

  await prisma.zone.delete({
    where: { id },
  });

  return NextResponse.json({
    success: true,
    data: null
  }, { status: 200 });
}

export const GET = withAuth(handleGET);
export const POST = withAuth(handlePOST);
export const PUT = withAuth(handlePUT);
export const DELETE = withAuth(handleDELETE); 