import { NextRequest, NextResponse } from "next/server";

type RouteContext = { params: Promise<{ path: string[] }> };
const apiBase = () => process.env.SMARTDOCTOR_API_INTERNAL_URL || "http://localhost:8000";
const secureCookie = process.env.APP_ENV === "production";

async function sendUpstream(target: URL, request: NextRequest, body: ArrayBuffer | undefined, accessToken?: string) {
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const correlationId = request.headers.get("x-correlation-id");
  if (contentType) headers.set("content-type", contentType);
  if (correlationId) headers.set("x-correlation-id", correlationId);
  if (accessToken) headers.set("authorization", `Bearer ${accessToken}`);
  return fetch(target, { method: request.method, headers, body, cache: "no-store", redirect: "manual" });
}

function refreshValue(upstream: Response): string | null {
  const headers = upstream.headers as Headers & { getSetCookie?: () => string[] };
  const all = headers.getSetCookie?.() || [upstream.headers.get("set-cookie") || ""];
  for (const item of all) {
    const match = item.match(/(?:^|[,;]\s*)smartdoctor_refresh=([^;]*)/);
    if (match) return decodeURIComponent(match[1]);
  }
  return null;
}

async function forward(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const apiPath = "/" + path.map(segment => encodeURIComponent(segment)).join("/");
  const allowed = apiPath.startsWith("/api/v1/workspace/") || apiPath.startsWith("/api/v1/patients/") ||
    apiPath.startsWith("/api/v1/super-admin/") || apiPath.startsWith("/api/v1/organizations/") ||
    apiPath.startsWith("/api/v1/clinic/") || apiPath.startsWith("/api/v1/themes/") ||
    apiPath.startsWith("/api/v1/super-admin/theme") || apiPath === "/api/v1/auth/users" ||
    apiPath.startsWith("/api/v1/auth/users/");
  if (!allowed) return NextResponse.json({ detail: "API route is not available through this proxy." }, { status: 404 });

  const accessToken = request.cookies.get("smartdoctor_access")?.value;
  const refreshToken = request.cookies.get("smartdoctor_refresh")?.value;
  const demoEnabled = process.env.APP_ENV === "development" && process.env.DEV_AUTH_ENABLED === "true";
  if (!accessToken && !refreshToken && !demoEnabled) {
    return NextResponse.json({ detail: "Authentication required." }, { status: 401 });
  }

  const target = new URL(apiPath + request.nextUrl.search, apiBase());
  const body = request.method === "GET" ? undefined : await request.arrayBuffer();
  let currentAccessToken = accessToken;
  let newAccessToken: string | undefined;
  let refreshedExpiresIn = 0;
  let refreshResponse: Response | undefined;

  if (!currentAccessToken && refreshToken) {
    refreshResponse = await fetch(`${apiBase()}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { cookie: `smartdoctor_refresh=${refreshToken}` },
      cache: "no-store",
    });
    if (refreshResponse.ok) {
      const session = await refreshResponse.json();
      newAccessToken = session.access_token;
      currentAccessToken = newAccessToken;
      refreshedExpiresIn = session.expires_in;
    } else {
      const response = NextResponse.json({ detail: "Your sign-in session expired. Please sign in again." }, { status: 401 });
      response.cookies.delete("smartdoctor_access");
      response.cookies.delete("smartdoctor_refresh");
      return response;
    }
  }

  let upstream = await sendUpstream(target, request, body, currentAccessToken);
  if (upstream.status === 401 && refreshToken && !newAccessToken) {
    refreshResponse = await fetch(`${apiBase()}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { cookie: `smartdoctor_refresh=${refreshToken}` },
      cache: "no-store",
    });
    if (refreshResponse.ok) {
      const session = await refreshResponse.json();
      newAccessToken = session.access_token;
      refreshedExpiresIn = session.expires_in;
      upstream = await sendUpstream(target, request, body, newAccessToken);
    }
  }

  const responseHeaders = new Headers();
  const upstreamType = upstream.headers.get("content-type");
  if (upstreamType) responseHeaders.set("content-type", upstreamType);
  responseHeaders.set("cache-control", "no-store");
  const response = new NextResponse(upstream.body, { status: upstream.status, headers: responseHeaders });

  if (upstream.status === 401) {
    response.cookies.delete("smartdoctor_access");
    response.cookies.delete("smartdoctor_refresh");
  }

  if (newAccessToken) {
    response.cookies.set("smartdoctor_access", newAccessToken, {
      httpOnly: true, secure: secureCookie, sameSite: "lax", path: "/", maxAge: refreshedExpiresIn,
    });
    const rotatedRefresh = refreshValue(refreshResponse!);
    if (rotatedRefresh) response.cookies.set("smartdoctor_refresh", rotatedRefresh, {
      httpOnly: true, secure: secureCookie, sameSite: "lax", path: "/", maxAge: 30 * 86400,
    });
  }
  return response;
}

export const GET = forward;
export const POST = forward;
export const PATCH = forward;
