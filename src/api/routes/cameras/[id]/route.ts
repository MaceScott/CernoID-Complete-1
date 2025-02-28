import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { logger } from '@/lib/logger'; // Assuming a logger utility is available

// Camera validation schema
const cameraSchema = z.object({
    name: z.string().min(1),
    location: z.string().min(1),
    type: z.enum(['indoor', 'outdoor']),
    resolution: z.string(),
});

// GET request handler
export async function GET(req: NextRequest, context: { params: { id: string } }) {
    try {
        const { id } = context.params;

        if (!id) {
            return NextResponse.json({ error: 'Camera ID is required' }, { status: 400 });
        }

        // TODO: Implement actual camera fetching logic
        return NextResponse.json({
            id,
            name: 'Camera 1',
            location: 'Main Entrance',
            type: 'outdoor',
            resolution: '1080p',
            status: 'active',
        });
    } catch (error) {
        logger.error('Failed to fetch camera', error);
        return NextResponse.json({ error: 'Failed to fetch camera' }, { status: 500 });
    }
}

// PATCH request handler
export async function PATCH(req: NextRequest, context: { params: { id: string } }) {
    try {
        const { id } = context.params;  // Correct way to access params
        const body = await req.json();
        const result = cameraSchema.partial().safeParse(body);

        if (!result.success) {
            return NextResponse.json({ error: "Invalid input", details: result.error.issues }, { status: 400 });
        }

        // TODO: Implement actual camera update logic
        return NextResponse.json({
            id,
            ...result.data,  // Updated data
        });
    } catch (error) {
        logger.error('Failed to update camera', error);
        return NextResponse.json({ error: 'Failed to update camera' }, { status: 500 });
    }
}
