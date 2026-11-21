import { NextRequest, NextResponse } from "next/server";

type RouteContext = { params: Promise<{ nextauth: string[] }> };
const apiBase = () => process.env.SMARTDOCTOR_API_INTERNAL_URL || "http://localhost:8000";
const secureCookie = process.env.APP_ENV === "production";

function cookieOptions(maxAge: number) {
  return { httpOnly: true, secure: secureCookie, sameSite: "lax" as const, path: "/", maxAge };
}

function refreshCookieValue(response: Response): string | null {
  const headers = response.headers as Headers & { getSetCookie?: () => string[] };
  const all = headers.getSetCookie?.() || [response.headers.get("set-cookie") || ""];
  for (const item of all) {
    const match = item.match(/(?:^|[,;]\s*)smartdoctor_refresh=([^;]*)/);
    if (match) return decodeURIComponent(match[1]);
  }
  return null;
}

async function callApi(path: string, method: string, body?: string, cookie?: string, accessToken?: string) {
  const headers = new Headers();
  if (body) headers.set("content-type", "application/json");
  if (cookie) headers.set("cookie", cookie);
  if (accessToken) headers.set("authorization", `Bearer ${accessToken}`);
  return fetch(`${apiBase()}/api/v1/auth/${path}`, {
    method, headers, body, cache: "no-store", redirect: "manual",
  });
}

function applySessionCookies(response: NextResponse, upstream: Response, accessToken: string, expiresIn: number) {
  response.cookies.set("smartdoctor_access", accessToken, cookieOptions(expiresIn));
  const refresh = refreshCookieValue(upstream);
  if (refresh !== null) response.cookies.set("smartdoctor_refresh", refresh, cookieOptions(30 * 86400));
}

async function handle(request: NextRequest, context: RouteContext, method: "GET" | "POST" | "PATCH") {
  const { nextauth = [] } = await context.params;
  const path = nextauth.join("/");
  const allowed = path === "me" || (method === "GET" && path === "users") || path === "login" || path === "register" ||
    path === "verify-email" || path === "resend-otp" || path === "refresh" ||
    path === "logout" || path === "forgot-password" || path === "reset-password" ||
    (method === "PATCH" && /^users\/[0-9a-f-]+\/role$/i.test(path));
  if (!allowed) return NextResponse.json({ detail: "Authentication route not found." }, { status: 404 });

  const refreshToken = request.cookies.get("smartdoctor_refresh")?.value;
  const cookie = refreshToken ? `smartdoctor_refresh=${refreshToken}` : undefined;
  const body = method === "GET" ? undefined : await request.text();

  if (path === "me" && method === "GET") {
    const access = request.cookies.get("smartdoctor_access")?.value;
    let upstream = access
      ? await callApi("me", "GET", undefined, undefined, access)
      : new Response(null, { status: 401 });
    if (upstream.status === 401 && cookie) {
      upstream = await callApi("refresh", "POST", undefined, cookie);
      if (upstream.ok) {
        const session = await upstream.json();
        const response = NextResponse.json(session.user, { headers: { "cache-control": "no-store" } });
        applySessionCookies(response, upstream, session.access_token, session.expires_in);
        return response;
      }
    }
    if (!upstream.ok) {
      const response = NextResponse.json({ detail: "Authentication required." }, { status: 401 });
      response.cookies.delete("smartdoctor_access");
      response.cookies.delete("smartdoctor_refresh");
      return response;
    }
    return NextResponse.json(await upstream.json(), { headers: { "cache-control": "no-store" } });
  }

  if (path === "logout" && method === "POST") {
    const upstream = await callApi("logout", "POST", undefined, cookie);
    const response = new NextResponse(null, { status: upstream.status === 204 ? 204 : 200 });
    response.cookies.delete("smartdoctor_access");
    response.cookies.delete("smartdoctor_refresh");
    return response;
  }

  const accessToken = request.cookies.get("smartdoctor_access")?.value;
  let upstream = await callApi(path, method, body, cookie, accessToken);
  let rotatedSession: { access_token: string; expires_in: number } | null = null;
  let rotatedResponse: Response | null = null;
  if (upstream.status === 401 && cookie && path !== "refresh") {
    rotatedResponse = await callApi("refresh", "POST", undefined, cookie);
    if (rotatedResponse.ok) {
      const session = await rotatedResponse.json();
      rotatedSession = session;
      upstream = await callApi(path, method, body, undefined, session.access_token);
    }
  }
  const payload = upstream.status === 204 ? null : await upstream.json().catch(() => ({}));
  if (!upstream.ok) return NextResponse.json(payload || { detail: "Authentication request failed." }, { status: upstream.status });

  if (rotatedSession && rotatedResponse) {
    const response = NextResponse.json(payload, { status: upstream.status, headers: { "cache-control": "no-store" } });
    applySessionCookies(response, rotatedResponse, rotatedSession.access_token, rotatedSession.expires_in);
    return response;
  }

  if ((path === "login" || path === "refresh") && payload?.access_token) {
    const response = NextResponse.json({ user: payload.user, expires_in: payload.expires_in }, {
      status: upstream.status, headers: { "cache-control": "no-store" },
    });
    applySessionCookies(response, upstream, payload.access_token, payload.expires_in);
    return response;
  }

  return NextResponse.json(payload, { status: upstream.status, headers: { "cache-control": "no-store" } });
}

export async function GET(request: NextRequest, context: RouteContext) {
  return handle(request, context, "GET");
}

export async function POST(request: NextRequest, context: RouteContext) {
  return handle(request, context, "POST");
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  return handle(request, context, "PATCH");
}
