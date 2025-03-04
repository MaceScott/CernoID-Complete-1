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

    const [total, accessPoints] = await Promise.all([
      prisma.accessPoint.count({ where }),
      prisma.accessPoint.findMany({
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
        },
      }),
    ]);

    return buildPaginationResponse(
      accessPoints,
      total,
      query.limit || 10,
      query.offset || 0
    );
  });
}

export async function POST(request: Request) {
  return withAdminAuth(async (user) => {
    const body = await request.json();
    const data = AccessPointSchema.parse(body);

    // Verify zone exists
    const zone = await prisma.securityZone.findUnique({
      where: { id: data.zoneId },
    });

    if (!zone) {
      throw new Error("Security zone not found");
    }

    const accessPoint = await prisma.accessPoint.create({
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

    return NextResponse.json(accessPoint, { status: 201 });
  });
}

export async function PUT(request: Request) {
  return withAdminAuth(async () => {
    const body = await request.json();
    const { id, ...data } = body;

    if (!id) {
      throw new Error("Access point ID is required");
    }

    const validatedData = AccessPointSchema.parse(data);

    // Verify zone exists if changing zone
    if (validatedData.zoneId) {
      const zone = await prisma.securityZone.findUnique({
        where: { id: validatedData.zoneId },
      });

      if (!zone) {
        throw new Error("Security zone not found");
      }
    }

    const accessPoint = await prisma.accessPoint.update({
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

    return accessPoint;
  });
}

export async function DELETE(request: Request) {
  return withAdminAuth(async () => {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get("id");

    if (!id) {
      throw new Error("Access point ID is required");
    }

    await prisma.accessPoint.delete({
      where: { id },
    });

    return { message: "Access point deleted successfully" };
  });
} 