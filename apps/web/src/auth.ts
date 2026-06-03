import type { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import { SignJWT } from "jose";

async function issueRankKitToken(user: {
  id?: string | null;
  email?: string | null;
  name?: string | null;
  image?: string | null;
}) {
  const secret = new TextEncoder().encode(process.env.NEXTAUTH_SECRET ?? "dev-nextauth-secret-change-me");
  const subject = user.email ?? user.id ?? "rankkit-user";

  return new SignJWT({
    email: user.email,
    name: user.name,
    image: user.image,
  })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(subject)
    .setIssuedAt()
    .setExpirationTime("8h")
    .sign(secret);
}

export const authOptions: NextAuthOptions = {
  session: {
    strategy: "jwt",
  },
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID ?? "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      const source = user ?? token;
      if (source.email) {
        token.rankkitAccessToken = await issueRankKitToken({
          id: source.id,
          email: source.email,
          name: source.name,
          image: "image" in source ? source.image : token.picture,
        });
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken =
        typeof token.rankkitAccessToken === "string" ? token.rankkitAccessToken : undefined;
      return session;
    },
  },
};
