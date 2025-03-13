import { NextResponse } from 'next/server';
import { ZodError, z } from 'zod';
import { getAuthToken } from './auth';
import type { NextRequest } from 'next/server';

export type ApiResponse<T = any> = {
  success: boolean;
  data?: T;
  error?: string;
};

export const PaginationSchema = z.object({
  page: z.coerce.number().min(1).default(1),
  limit: z.coerce.number().min(1).max(100).default(10),
  sort: z.string().optional(),
  order: z.enum(['asc', 'desc']).optional(),
  search: z.string().optional(),
});

export type PaginationParams = z.infer<typeof PaginationSchema>;

export function parseQueryParams<T extends z.ZodType>(
  searchParams: URLSearchParams | NextRequest,
  schema: T
): z.infer<T> {
  const params = searchParams instanceof URLSearchParams
    ? Object.fromEntries(searchParams)
    : Object.fromEntries(searchParams.nextUrl.searchParams);
  return schema.parse(params);
}

export function buildPaginationResponse<T>(
  items: T[],
  total: number,
  params: PaginationParams
) {
  const { page, limit } = params;
  return {
    items,
    total,
    page,
    limit,
    pages: Math.ceil(total / limit),
  };
}

export function handleError(error: unknown): NextResponse<ApiResponse> {
  console.error('API Error:', error);

  if (error instanceof ZodError) {
    return NextResponse.json(
      { success: false, error: 'Validation error', data: error.errors },
      { status: 400 }
    );
  }

  if (error instanceof Error) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }

  return NextResponse.json(
    { success: false, error: 'An unexpected error occurred' },
    { status: 500 }
  );
}

export function successResponse<T>(data: T): NextResponse<ApiResponse<T>> {
  return NextResponse.json({ success: true, data }, { status: 200 });
}

export function errorResponse(message: string, status: number = 400): NextResponse<ApiResponse> {
  return NextResponse.json(
    { success: false, error: message },
    { status }
  );
}

export async function withAuth<T>(
  request: NextRequest,
  handler: (user: any) => Promise<NextResponse<ApiResponse<T>>>
): Promise<NextResponse<ApiResponse<T>>> {
  try {
    const token = await getAuthToken(request);
    if (!token) {
      return errorResponse('Unauthorized', 401);
    }
    return await handler(token);
  } catch (error) {
    return handleError(error);
  }
}

export async function withAdminAuth<T>(
  request: NextRequest,
  handler: (user: any) => Promise<NextResponse<ApiResponse<T>>>
): Promise<NextResponse<ApiResponse<T>>> {
  try {
    const token = await getAuthToken(request);
    if (!token) {
      return errorResponse('Unauthorized', 401);
    }
    if (!token.isAdmin) {
      return errorResponse('Forbidden', 403);
    }
    return await handler(token);
  } catch (error) {
    return handleError(error);
  }
} 