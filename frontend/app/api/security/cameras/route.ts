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

export async function GET(request: NextRequest) {
  return withAuth(request, async (session) => {
    const query = parseQueryParams(request, QuerySchema);
    const { page, limit } = query;
    const skip = (page - 1) * limit;

    const where = {
      ...(query.name && { name: { contains: query.name } }),
      ...(query.location && { location: query.location }),
      ...(query.status && { status: query.status }),
    };

    const [total, cameras] = await Promise.all([
      prisma.camera.count({ where }),
      prisma.camera.findMany({
        where,
        take: limit,
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
      data: buildPaginationResponse(cameras, total, query)
    }, { status: 200 });
  });
}

export async function POST(request: NextRequest) {
  return withAuth(request, async (session) => {
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
          createdBy: session.id,
          updatedBy: session.id,
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
  });
}

export async function PUT(request: NextRequest) {
  return withAuth(request, async (session) => {
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
          updatedBy: session.id,
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
  });
}

export async function DELETE(request: NextRequest) {
  return withAuth(request, async () => {
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
  });
} 