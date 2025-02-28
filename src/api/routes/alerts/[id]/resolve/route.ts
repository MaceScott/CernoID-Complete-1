import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

// Define validation schema
const schema = z.object({
    name: z.string().min(1),
    email: z.string().email(),
});

// GET request handler
export async function GET(req: NextRequest, context: { params: { id: string } }) {
    const { id } = context.params;

    if (!id) {
        return NextResponse.json({ error: 'User ID is required' }, { status: 400 });
    }

    // Simulate fetching user data
    return NextResponse.json({
        id,
        name: 'User 1',
        email: 'user1@example.com',
    }, { status: 200 });
}

// PATCH request handler
export async function PATCH(req: NextRequest, context: { params: { id: string } }) {
    const { id } = context.params;

    if (!id) {
        return NextResponse.json({ error: 'ID is required' }, { status: 400 });
    }

    const body = await req.json();
    const result = schema.partial().safeParse(body);

    if (!result.success) {
        return NextResponse.json({ error: 'Invalid input', details: result.error.issues }, { status: 400 });
    }

    // Logic to handle the request...

    return NextResponse.json({ success: true, message: `User ${id} updated`, data: result.data }, { status: 200 });
}

// POST request handler
export async function POST(req: NextRequest, context: { params: { id: string } }) {
    const { id } = context.params;

    if (!id) {
        return NextResponse.json({ error: 'ID is required' }, { status: 400 });
    }

    const body = await req.json();
    const result = schema.safeParse(body);

    if (!result.success) {
        return NextResponse.json({ error: 'Invalid input', details: result.error.issues }, { status: 400 });
    }

    return NextResponse.json({ success: true, message: `User ${id} created` }, { status: 201 });
}

export async function DELETE(req: NextRequest, context: { params: { id: string } }) {
    const { id } = context.params;

    if (!id) {
        return NextResponse.json({ error: 'ID is required' }, { status: 400 });
    }

    // Logic to delete the user...

    return NextResponse.json({ success: true, message: `User ${id} deleted` }, { status: 200 });
}
