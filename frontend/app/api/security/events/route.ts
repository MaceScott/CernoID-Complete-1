import { NextResponse } from 'next/server'
import { z } from 'zod'
import { prisma } from '../../../lib/prisma'
import type { NextRequest } from 'next/server'
import { 
  withAuth, 
  parseQueryParams, 
  buildPaginationResponse,
  PaginationSchema,
} from '../../../lib/api-utils'

const QuerySchema = PaginationSchema.extend({
  startDate: z.string().optional(),
  endDate: z.string().optional(),
  sourceType: z.string().optional(),
  severity: z.enum(['low', 'medium', 'high']).optional(),
  status: z.enum(['open', 'closed', 'in_progress']).optional(),
  assignedTo: z.string().optional(),
});

async function handleGET(request: NextRequest): Promise<Response> {
  const query = parseQueryParams(request, QuerySchema);
  const { page, pageSize } = query;
  const skip = (page - 1) * pageSize;

  const where = {
    ...(query.startDate && {
      createdAt: { gte: new Date(query.startDate) },
    }),
    ...(query.endDate && {
      createdAt: { 
        ...((query.startDate && { gte: new Date(query.startDate) }) || {}),
        lte: new Date(query.endDate),
      },
    }),
    ...(query.sourceType && { sourceType: query.sourceType }),
    ...(query.severity && { severity: query.severity }),
    ...(query.status && { status: query.status }),
    ...(query.assignedTo && { assignedTo: query.assignedTo }),
  };

  const [total, alerts] = await Promise.all([
    prisma.alert.count({ where }),
    prisma.alert.findMany({
      where,
      orderBy: { createdAt: 'desc' },
      take: pageSize,
      skip,
      include: {
        creator: true,
        assignedUser: true,
        camera: true,
        accessPoint: true,
      },
    }),
  ]);

  return NextResponse.json({ 
    success: true, 
    data: buildPaginationResponse(alerts, total, page, pageSize)
  }, { status: 200 });
}

async function handlePOST(request: NextRequest): Promise<Response> {
  const data = await request.json();
  
  const alert = await prisma.alert.create({
    data: {
      ...data,
      createdBy: request.headers.get('x-user-id') || '',
      updatedBy: request.headers.get('x-user-id') || '',
    },
    include: {
      creator: true,
      assignedUser: true,
      camera: true,
      accessPoint: true,
    },
  });

  return NextResponse.json({ 
    success: true, 
    data: alert 
  }, { status: 201 });
}

export const GET = withAuth(handleGET);
export const POST = withAuth(handlePOST); 