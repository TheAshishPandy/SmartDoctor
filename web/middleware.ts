import { NextResponse } from "next/server";
import { auth } from "./auth";

const publicPaths = new Set(["/login", "/register", "/forgot-password"]);

export default auth((request) => {
  const pathname = request.nextUrl.pathname;
  const demoEnabled = process.env.APP_ENV === "development" && process.env.DEV_AUTH_ENABLED === "true";
  const isApi = pathname.startsWith("/api/backend/");
  const sessionError = request.auth?.error;
  if (sessionError || (!request.auth && !demoEnabled)) {
    if (isApi) {
      return NextResponse.json(
        { detail: sessionError ? "Your sign-in session expired. Please sign in again." : "Authentication required." },
        { status: 401 },
      );
    }
    const login = new URL("/login", request.nextUrl);
    login.searchParams.set("callbackUrl", pathname + request.nextUrl.search);
    return NextResponse.redirect(login);
  }
  if (request.auth && publicPaths.has(pathname)) {
    return NextResponse.redirect(new URL("/", request.nextUrl));
  }
  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!api/auth|_next/static|_next/image|favicon.ico).*)"],
};