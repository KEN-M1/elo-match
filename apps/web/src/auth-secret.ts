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
