import { NextRequest, NextResponse } from "next/server";

const publicPaths = new Set(["/login", "/register", "/forgot-password"]);

export default function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const demoEnabled = process.env.APP_ENV === "development" && process.env.DEV_AUTH_ENABLED === "true";
  const isApi = pathname.startsWith("/api/backend/");
  const isPublicPath = publicPaths.has(pathname);
  const authenticated = Boolean(
    request.cookies.get("smartdoctor_access")?.value ||
    request.cookies.get("smartdoctor_refresh")?.value
  );

  if (isPublicPath) {
    if (authenticated) return NextResponse.redirect(new URL("/", request.nextUrl));
    return NextResponse.next();
  }

  // The demo workspace remains available only in explicitly enabled local development.
  if (demoEnabled && !authenticated) return NextResponse.next();

  if (isApi && !authenticated) {
    return NextResponse.json({ detail: "Authentication required." }, { status: 401 });
  }

  if (!authenticated) {
    const login = new URL("/login", request.nextUrl);
    login.searchParams.set("callbackUrl", pathname + request.nextUrl.search);
    return NextResponse.redirect(login);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api/auth|_next/static|_next/image|favicon.ico).*)"],
};
