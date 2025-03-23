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

const CameraSchema = z.object({
  name: z.string(),
  url: z.string(),
  location: z.string().optional(),
  status: z.enum(["offline", "online"]).default("offline"),
});

const QuerySchema = PaginationSchema.extend({
  name: z.string().optional(),
  location: z.string().optional(),
  status: z.enum(["offline", "online"]).optional(),
});

type QueryParams = z.infer<typeof QuerySchema>;

async function handleGET(request: NextRequest): Promise<Response> {
  const query = parseQueryParams(request, QuerySchema);
  const { page, pageSize } = query;
  const skip = (page - 1) * pageSize;

  const where = {
    ...(query.name && { name: { contains: query.name } }),
    ...(query.location && { location: query.location }),
    ...(query.status && { status: query.status }),
  };

  const [total, cameras] = await Promise.all([
    prisma.camera.count({ where }),
    prisma.camera.findMany({
      where,
      take: pageSize,
      skip,
      orderBy: { createdAt: 'desc' },
      include: {
        alerts: {
          select: {
            id: true,
            title: true,
            severity: true,
            description: true,
            createdAt: true,
            status: true,
            sourceType: true,
          },
        },
        creator: {
          select: {
            id: true,
            name: true,
            email: true,
          },
        },
      },
    }),
  ]);

  return NextResponse.json({
    success: true,
    data: buildPaginationResponse(cameras, total, page, pageSize)
  }, { status: 200 });
}

async function handlePOST(request: NextRequest): Promise<Response> {
  const body = await request.json();
  const data = CameraSchema.parse(body);

  const existingCamera = await prisma.camera.findFirst({
    where: {
      name: data.name,
    },
  });

  if (existingCamera) {
    return NextResponse.json({
      success: false,
      error: 'Camera already exists'
    }, { status: 409 });
  }

  try {
    const camera = await prisma.camera.create({
      data: {
        ...data,
        createdBy: request.headers.get('x-user-id') || '',
        updatedBy: request.headers.get('x-user-id') || '',
      },
    });

    return NextResponse.json({
      success: true,
      data: camera
    }, { status: 201 });
  } catch (error) {
    console.error('Failed to create camera:', error);
    return NextResponse.json({
      success: false,
      error: "Failed to create camera"
    }, { status: 500 });
  }
}

async function handlePUT(request: NextRequest): Promise<Response> {
  const body = await request.json();
  const { id, ...data } = body;

  if (!id) {
    return NextResponse.json({
      success: false,
      error: 'Camera ID is required'
    }, { status: 400 });
  }

  const validatedData = CameraSchema.parse(data);

  try {
    const camera = await prisma.camera.update({
      where: { id },
      data: {
        ...validatedData,
        updatedBy: request.headers.get('x-user-id') || '',
      },
    });

    return NextResponse.json({
      success: true,
      data: camera
    }, { status: 200 });
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: 'Failed to update camera'
    }, { status: 500 });
  }
}

async function handleDELETE(request: NextRequest): Promise<Response> {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get('id');

  if (!id) {
    return NextResponse.json({
      success: false,
      error: 'Camera ID is required'
    }, { status: 400 });
  }

  try {
    await prisma.camera.delete({
      where: { id },
    });

    return NextResponse.json({
      success: true,
      message: 'Camera deleted successfully'
    }, { status: 200 });
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: 'Failed to delete camera'
    }, { status: 500 });
  }
}

export const GET = withAuth(handleGET);
export const POST = withAuth(handlePOST);
export const PUT = withAuth(handlePUT);
export const DELETE = withAuth(handleDELETE); 