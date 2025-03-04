import { NextResponse } from "next/server";
import { z } from "zod";
import { getCurrentUser } from "./auth";

export type ApiResponse<T> = {
  data?: T;
  error?: string;
  details?: unknown;
};

export async function withAuth<T>(
  handler: (user: Awaited<ReturnType<typeof getCurrentUser>>) => Promise<T>
): Promise<NextResponse> {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }
    const result = await handler(user);
    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
}

export async function withAdminAuth<T>(
  handler: (user: Awaited<ReturnType<typeof getCurrentUser>>) => Promise<T>
): Promise<NextResponse> {
  try {
    const user = await getCurrentUser();
    if (!user?.isAdmin) {
      return NextResponse.json(
        { error: "Unauthorized - Admin access required" },
        { status: 401 }
      );
    }
    const result = await handler(user);
    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
}

export function handleApiError(error: unknown): NextResponse {
  console.error("API Error:", error);
  
  if (error instanceof z.ZodError) {
    return NextResponse.json(
      { 
        error: "Validation error", 
        details: error.errors 
      },
      { status: 400 }
    );
  }

  if (error instanceof Error) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    );
  }

  return NextResponse.json(
    { error: "Internal server error" },
    { status: 500 }
  );
}

export function parseQueryParams<T extends z.ZodType>(
  searchParams: URLSearchParams,
  schema: T
): z.infer<T> {
  const params = Object.fromEntries(searchParams);
  return schema.parse(params);
}

export function buildPaginationResponse<T>(
  data: T[],
  total: number,
  limit: number,
  offset: number
) {
  return {
    data,
    total,
    limit,
    offset,
    hasMore: offset + data.length < total,
  };
}

export const PaginationSchema = z.object({
  limit: z.string().transform(Number).optional(),
  offset: z.string().transform(Number).optional(),
}); 