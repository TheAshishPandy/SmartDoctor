import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";

type RouteContext = { params: Promise<{ path: string[] }> };

async function forward(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const apiPath = "/" + path.map(segment => encodeURIComponent(segment)).join("/");
  const allowed = apiPath.startsWith("/api/v1/workspace/") || apiPath.startsWith("/api/v1/patients/");
  if (!allowed) return NextResponse.json({ detail: "API route is not available through this proxy." }, { status: 404 });

  const token = await getToken({ req: request, secret: process.env.AUTH_SECRET });
  const accessToken = typeof token?.accessToken === "string" ? token.accessToken : "";
  const demoEnabled = process.env.APP_ENV === "development" && process.env.DEV_AUTH_ENABLED === "true";
  if (!accessToken && !demoEnabled) {
    return NextResponse.json({ detail: "Authentication required." }, { status: 401 });
  }
  if (token?.authError || (typeof token?.accessTokenExpires === "number" && Date.now() >= token.accessTokenExpires)) {
    return NextResponse.json({ detail: "Your access token expired. Please sign in again." }, { status: 401 });
  }

  const baseUrl = process.env.SMARTDOCTOR_API_INTERNAL_URL || "http://localhost:8000";
  const target = new URL(apiPath + request.nextUrl.search, baseUrl);
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const correlationId = request.headers.get("x-correlation-id");
  if (contentType) headers.set("content-type", contentType);
  if (correlationId) headers.set("x-correlation-id", correlationId);
  if (accessToken) headers.set("authorization", "Bearer " + accessToken);

  const method = request.method;
  const body = method === "GET" ? undefined : await request.arrayBuffer();
  try {
    const upstream = await fetch(target, { method, headers, body, cache: "no-store", redirect: "manual" });
    const responseHeaders = new Headers();
    const upstreamType = upstream.headers.get("content-type");
    if (upstreamType) responseHeaders.set("content-type", upstreamType);
    responseHeaders.set("cache-control", "no-store");
    return new NextResponse(upstream.body, { status: upstream.status, headers: responseHeaders });
  } catch {
    return NextResponse.json({ detail: "SmartDoctor API is unavailable." }, { status: 502 });
  }
}

export const GET = forward;
export const POST = forward;