import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { 
  withAuth, 
  withAdminAuth,
  parseQueryParams, 
  buildPaginationResponse,
  PaginationSchema 
} from "@/lib/api-utils";

const AlertSchema = z.object({
  type: z.string(),
  severity: z.string(),
  message: z.string(),
  status: z.enum(["open", "resolved", "dismissed"]).default("open"),
  cameraId: z.string().optional(),
  resolvedAt: z.date().optional(),
  resolvedBy: z.string().optional(),
});

const QuerySchema = PaginationSchema.extend({
  type: z.string().optional(),
  severity: z.string().optional(),
  status: z.enum(["open", "resolved", "dismissed"]).optional(),
  cameraId: z.string().optional(),
  userId: z.string().optional(),
  startDate: z.string().optional(),
  endDate: z.string().optional(),
});

export async function GET(request: Request) {
  return withAuth(async () => {
    const { searchParams } = new URL(request.url);
    const query = parseQueryParams(searchParams, QuerySchema);

    const where = {
      ...(query.type && { type: query.type }),
      ...(query.severity && { severity: query.severity }),
      ...(query.status && { status: query.status }),
      ...(query.cameraId && { cameraId: query.cameraId }),
      ...(query.userId && { userId: query.userId }),
      ...(query.startDate && {
        createdAt: { gte: new Date(query.startDate) },
      }),
      ...(query.endDate && {
        createdAt: { 
          ...((query.startDate && { gte: new Date(query.startDate) }) || {}),
          lte: new Date(query.endDate),
        },
      }),
    };

    const [total, alerts] = await Promise.all([
      prisma.alert.count({ where }),
      prisma.alert.findMany({
        where,
        take: query.limit || 10,
        skip: query.offset || 0,
        orderBy: { createdAt: "desc" },
        include: {
          camera: {
            select: {
              id: true,
              name: true,
              type: true,
              location: true,
              status: true,
            },
          },
          user: {
            select: {
              id: true,
              name: true,
              email: true,
            },
          },
        },
      }),
    ]);

    return buildPaginationResponse(
      alerts,
      total,
      query.limit || 10,
      query.offset || 0
    );
  });
}

export async function POST(request: Request) {
  return withAuth(async (user) => {
    if (!user) throw new Error("User is required");

    const body = await request.json();
    const data = AlertSchema.parse(body);

    // Verify camera exists if provided
    if (data.cameraId) {
      const camera = await prisma.camera.findUnique({
        where: { id: data.cameraId },
      });

      if (!camera) {
        throw new Error("Camera not found");
      }
    }

    const alert = await prisma.alert.create({
      data: {
        ...data,
        userId: user.id,
      },
      include: {
        camera: {
          select: {
            id: true,
            name: true,
            type: true,
            location: true,
            status: true,
          },
        },
        user: {
          select: {
            id: true,
            name: true,
            email: true,
          },
        },
      },
    });

    return NextResponse.json(alert, { status: 201 });
  });
}

export async function PUT(request: Request) {
  return withAuth(async (user) => {
    if (!user) throw new Error("User is required");

    const body = await request.json();
    const { id, ...data } = body;

    if (!id) {
      throw new Error("Alert ID is required");
    }

    const validatedData = AlertSchema.parse(data);

    // Verify camera exists if changing camera
    if (validatedData.cameraId) {
      const camera = await prisma.camera.findUnique({
        where: { id: validatedData.cameraId },
      });

      if (!camera) {
        throw new Error("Camera not found");
      }
    }

    // If resolving the alert, add resolution details
    if (validatedData.status === "resolved" && !validatedData.resolvedAt) {
      validatedData.resolvedAt = new Date();
      validatedData.resolvedBy = user.id;
    }

    const alert = await prisma.alert.update({
      where: { id },
      data: validatedData,
      include: {
        camera: {
          select: {
            id: true,
            name: true,
            type: true,
            location: true,
            status: true,
          },
        },
        user: {
          select: {
            id: true,
            name: true,
            email: true,
          },
        },
      },
    });

    return alert;
  });
}

export async function DELETE(request: Request) {
  return withAdminAuth(async () => {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get("id");

    if (!id) {
      throw new Error("Alert ID is required");
    }

    await prisma.alert.delete({
      where: { id },
    });

    return { message: "Alert deleted successfully" };
  });
} 