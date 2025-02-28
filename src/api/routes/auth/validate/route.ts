import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  try {
    // Extract token from request headers
    const authHeader = req.headers.get("Authorization");

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json({ error: "Unauthorized - No Token Provided" }, { status: 401 });
    }

    const token = authHeader.split("Bearer ")[1];

    // Check if token exists (for now, log it for debugging)
    console.log("Received Token:", token);

    // TODO: Replace with actual authentication logic (JWT verification)
    if (token !== "valid-token") {
      return NextResponse.json({ error: "Forbidden - Invalid Token" }, { status: 403 });
    }

    return NextResponse.json({ success: true, message: "User is authenticated" });
  } catch (error) {
    console.error("Validation Error:", error);
    return NextResponse.json({ error: "Server Error" }, { status: 500 });
  }
}