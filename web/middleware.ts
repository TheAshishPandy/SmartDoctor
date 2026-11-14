import { NextResponse } from "next/server";
import { auth } from "./auth";

const publicPaths = new Set([
  "/login",
  "/register",
  "/forgot-password",
]);

export default auth((request) => {
  const pathname = request.nextUrl.pathname;

  const demoEnabled =
    process.env.APP_ENV === "development" &&
    process.env.DEV_AUTH_ENABLED === "true";

  const isApi = pathname.startsWith("/api/backend/");
  const isPublicPath = publicPaths.has(pathname);
  const sessionError = request.auth?.error;
  const isAuthenticated =
    Boolean(request.auth?.user) && !sessionError;

  // Authentication pages must be reachable without an active session.
  // This check must run before the protected-route redirect.
  if (isPublicPath) {
    if (isAuthenticated) {
      return NextResponse.redirect(new URL("/", request.nextUrl));
    }

    return NextResponse.next();
  }

  // Preserve the local synthetic-demo bypass in development.
  if (demoEnabled && !sessionError) {
    return NextResponse.next();
  }

  // Return JSON 401 responses for protected backend API requests.
  if (isApi && !isAuthenticated) {
    return NextResponse.json(
      {
        detail: sessionError
          ? "Your sign-in session expired. Please sign in again."
          : "Authentication required.",
      },
      { status: 401 },
    );
  }

  // Redirect unauthenticated users to login with their original destination.
  if (!isAuthenticated) {
    const login = new URL("/login", request.nextUrl);
    const callbackUrl = pathname + request.nextUrl.search;

    // Do not create a callback that points back to the login page.
    if (pathname !== "/login") {
      login.searchParams.set("callbackUrl", callbackUrl);
    }

    return NextResponse.redirect(login);
  }

  return NextResponse.next();
});

export const config = {
  matcher: [
    "/((?!api/auth|_next/static|_next/image|favicon.ico).*)",
  ],
};
