const DEVELOPMENT_NEXTAUTH_SECRET = "dev-nextauth-secret-change-me";

export function requireNextAuthSecret() {
  const secret = process.env.NEXTAUTH_SECRET;
  if (secret) {
    return secret;
  }

  if (process.env.NODE_ENV === "production") {
    throw new Error("NEXTAUTH_SECRET must be set in production.");
  }

  return DEVELOPMENT_NEXTAUTH_SECRET;
}

export function requireGoogleOAuthCredentials() {
  const clientId = process.env.GOOGLE_CLIENT_ID ?? "";
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET ?? "";

  if (clientId && clientSecret) {
    return { clientId, clientSecret };
  }

  if (process.env.AUTH_REQUIRED === "true") {
    throw new Error("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set when AUTH_REQUIRED=true.");
  }

  return { clientId, clientSecret };
}
