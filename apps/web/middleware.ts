import { getToken } from "next-auth/jwt";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { requireNextAuthSecret } from "./src/auth-secret";

const protectedPrefixes = ["/dashboard", "/leagues", "/invites"];

function authIsRequired() {
  return process.env.AUTH_REQUIRED === "true";
}

function shouldProtect(pathname: string) {
  return protectedPrefixes.some((prefix) => pathname.startsWith(prefix));
}

export default async function middleware(request: NextRequest) {
  if (!authIsRequired() || !shouldProtect(request.nextUrl.pathname)) {
    return NextResponse.next();
  }

  const token = await getToken({
    req: request,
    secret: requireNextAuthSecret(),
  });

  if (token) {
    return NextResponse.next();
  }

  const redirectUrl = request.nextUrl.clone();
  redirectUrl.pathname = "/sign-in";
  redirectUrl.searchParams.set("callbackUrl", request.nextUrl.pathname);

  return NextResponse.redirect(redirectUrl);
}

export const config = {
  matcher: ["/dashboard/:path*", "/leagues/:path*", "/invites/:path*"],
};
