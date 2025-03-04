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

const CameraSchema = z.object({
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
});

export async function GET(request: Request) {
  return withAuth(async () => {
    const { searchParams } = new URL(request.url);
    const query = parseQueryParams(searchParams, QuerySchema);

    const where = {
      ...(query.name && { name: { contains: query.name } }),
      ...(query.type && { type: query.type }),
      ...(query.location && { location: query.location }),
      ...(query.status && { status: query.status }),
      ...(query.zoneId && { zoneId: query.zoneId }),
    };

    const [total, cameras] = await Promise.all([
      prisma.camera.count({ where }),
      prisma.camera.findMany({
        where,
        take: query.limit || 10,
        skip: query.offset || 0,
        orderBy: { name: "asc" },
        include: {
          zone: {
            select: {
              id: true,
              name: true,
              level: true,
            },
          },
          alerts: {
            where: { status: "open" },
            select: {
              id: true,
              type: true,
              severity: true,
              message: true,
              createdAt: true,
            },
            take: 5,
            orderBy: { createdAt: "desc" },
          },
        },
      }),
    ]);

    return buildPaginationResponse(
      cameras,
      total,
      query.limit || 10,
      query.offset || 0
    );
  });
}

export async function POST(request: Request) {
  return withAdminAuth(async (user) => {
    const body = await request.json();
    const data = CameraSchema.parse(body);

    // Verify zone exists
    const zone = await prisma.securityZone.findUnique({
      where: { id: data.zoneId },
    });

    if (!zone) {
      throw new Error("Security zone not found");
    }

    const camera = await prisma.camera.create({
      data: {
        ...data,
      },
      include: {
        zone: {
          select: {
            id: true,
            name: true,
            level: true,
          },
        },
      },
    });

    return NextResponse.json(camera, { status: 201 });
  });
}

export async function PUT(request: Request) {
  return withAdminAuth(async () => {
    const body = await request.json();
    const { id, ...data } = body;

    if (!id) {
      throw new Error("Camera ID is required");
    }

    const validatedData = CameraSchema.parse(data);

    // Verify zone exists if changing zone
    if (validatedData.zoneId) {
      const zone = await prisma.securityZone.findUnique({
        where: { id: validatedData.zoneId },
      });

      if (!zone) {
        throw new Error("Security zone not found");
      }
    }

    const camera = await prisma.camera.update({
      where: { id },
      data: validatedData,
      include: {
        zone: {
          select: {
            id: true,
            name: true,
            level: true,
          },
        },
      },
    });

    return camera;
  });
}

export async function DELETE(request: Request) {
  return withAdminAuth(async () => {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get("id");

    if (!id) {
      throw new Error("Camera ID is required");
    }

    // Check if camera has open alerts
    const camera = await prisma.camera.findUnique({
      where: { id },
      include: {
        alerts: {
          where: { status: "open" },
        },
      },
    });

    if (camera?.alerts.length) {
      throw new Error("Cannot delete camera with open alerts");
    }

    await prisma.camera.delete({
      where: { id },
    });

    return { message: "Camera deleted successfully" };
  });
} 