import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { prisma } from '@/lib/prisma';
import { Prisma } from '@prisma/client';
import { 
  withAuth, 
  parseQueryParams, 
  buildPaginationResponse,
  PaginationSchema,
  type ApiResponse
} from '@/lib/api-utils';
import type { InputJsonValue } from '@prisma/client/runtime/library';

const AlertSchema = z.object({
  title: z.string().min(1),
  description: z.string().optional(),
  severity: z.enum(['low', 'medium', 'high', 'critical']),
  status: z.enum(['open', 'acknowledged', 'resolved', 'false_positive']),
  sourceType: z.enum(['camera', 'access_point', 'manual']),
  cameraId: z.string().optional(),
  accessPointId: z.string().optional(),
  metadata: z.record(z.unknown()).optional(),
  assignedTo: z.string().optional(),
});

const QuerySchema = PaginationSchema.extend({
  status: z.enum(['open', 'acknowledged', 'resolved', 'false_positive']).optional(),
  severity: z.enum(['low', 'medium', 'high', 'critical']).optional(),
  sourceType: z.enum(['camera', 'access_point', 'manual']).optional(),
  cameraId: z.string().optional(),
  accessPointId: z.string().optional(),
  assignedTo: z.string().optional(),
  startDate: z.string().datetime().optional(),
  endDate: z.string().datetime().optional(),
});

export async function GET(request: NextRequest) {
  return withAuth(request, async (session) => {
    const query = parseQueryParams(request, QuerySchema);
    const { page, limit } = query;
    const skip = (page - 1) * limit;

    const where = {
      ...(query.status && { status: query.status }),
      ...(query.severity && { severity: query.severity }),
      ...(query.sourceType && { sourceType: query.sourceType }),
      ...(query.cameraId && { cameraId: query.cameraId }),
      ...(query.accessPointId && { accessPointId: query.accessPointId }),
      ...(query.assignedTo && { assignedTo: query.assignedTo }),
      ...(query.startDate && query.endDate && {
        createdAt: {
          gte: new Date(query.startDate),
          lte: new Date(query.endDate),
        },
      }),
    };

    const [total, alerts] = await Promise.all([
      prisma.alert.count({ where }),
      prisma.alert.findMany({
        where,
        take: limit,
        skip,
        orderBy: { createdAt: 'desc' },
        include: {
          assignedUser: {
            select: {
              id: true,
              name: true,
              email: true,
            },
          },
          camera: {
            select: {
              id: true,
              name: true,
              location: true,
            },
          },
          accessPoint: {
            select: {
              id: true,
              name: true,
              location: true,
            },
          },
        },
      }),
    ]);

    return NextResponse.json({
      success: true,
      data: buildPaginationResponse(alerts, total, query)
    }, { status: 200 });
  });
}

export async function POST(request: NextRequest) {
  return withAuth(request, async (session) => {
    const body = await request.json();
    const data = AlertSchema.parse(body);

    if (data.cameraId || data.accessPointId) {
      const source = await (async () => {
        switch (data.sourceType) {
          case 'camera':
            return data.cameraId ? prisma.camera.findUnique({ where: { id: data.cameraId } }) : null;
          case 'access_point':
            return data.accessPointId ? prisma.accessPoint.findUnique({ where: { id: data.accessPointId } }) : null;
          default:
            return null;
        }
      })();

      if (!source) {
        return NextResponse.json({
          success: false,
          error: `${data.sourceType} not found`
        }, { status: 404 });
      }
    }

    try {
      const alert = await prisma.alert.create({
        data: {
          title: data.title,
          description: data.description,
          severity: data.severity,
          status: data.status,
          sourceType: data.sourceType,
          metadata: data.metadata ? (data.metadata as InputJsonValue) : undefined,
          createdBy: session.id,
          updatedBy: session.id,
          creator: {
            connect: { id: session.id }
          },
          ...(data.assignedTo && {
            assignedUser: {
              connect: { id: data.assignedTo }
            }
          }),
          ...(data.sourceType === 'camera' && data.cameraId && {
            camera: {
              connect: { id: data.cameraId }
            }
          }),
          ...(data.sourceType === 'access_point' && data.accessPointId && {
            accessPoint: {
              connect: { id: data.accessPointId }
            }
          }),
        },
      });

      return NextResponse.json({
        success: true,
        data: alert
      }, { status: 201 });
    } catch (error) {
      return NextResponse.json({
        success: false,
        error: 'Failed to create alert'
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
        error: 'Alert ID is required'
      }, { status: 400 });
    }

    const validatedData = AlertSchema.parse(data);

    if (validatedData.cameraId || validatedData.accessPointId) {
      const source = await (async () => {
        switch (validatedData.sourceType) {
          case 'camera':
            return validatedData.cameraId ? prisma.camera.findUnique({ where: { id: validatedData.cameraId } }) : null;
          case 'access_point':
            return validatedData.accessPointId ? prisma.accessPoint.findUnique({ where: { id: validatedData.accessPointId } }) : null;
          default:
            return null;
        }
      })();

      if (!source) {
        return NextResponse.json({
          success: false,
          error: `${validatedData.sourceType} not found`
        }, { status: 404 });
      }
    }

    if (validatedData.assignedTo) {
      const user = await prisma.user.findUnique({
        where: { id: validatedData.assignedTo },
      });

      if (!user) {
        return NextResponse.json({
          success: false,
          error: 'Assigned user not found'
        }, { status: 404 });
      }
    }

    try {
      const alert = await prisma.alert.update({
        where: { id },
        data: {
          title: validatedData.title,
          description: validatedData.description,
          severity: validatedData.severity,
          status: validatedData.status,
          sourceType: validatedData.sourceType,
          cameraId: validatedData.cameraId || null,
          accessPointId: validatedData.accessPointId || null,
          metadata: validatedData.metadata ? (validatedData.metadata as InputJsonValue) : undefined,
          assignedTo: validatedData.assignedTo || null,
          updatedBy: session.id,
        },
      });

      return NextResponse.json({
        success: true,
        data: alert
      }, { status: 200 });
    } catch (error) {
      return NextResponse.json({
        success: false,
        error: 'Failed to update alert'
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
        error: 'Alert ID is required'
      }, { status: 400 });
    }

    try {
      await prisma.alert.delete({
        where: { id },
      });

      return NextResponse.json({
        success: true,
        message: 'Alert deleted successfully'
      }, { status: 200 });
    } catch (error) {
      return NextResponse.json({
        success: false,
        error: 'Failed to delete alert'
      }, { status: 500 });
    }
  });
} 