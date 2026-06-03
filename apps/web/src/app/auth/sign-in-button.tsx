"use client";

import { signIn, signOut, useSession } from "next-auth/react";

export function SignInButton() {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return <span className="muted">Checking session...</span>;
  }

  if (session?.user) {
    return (
      <button className="button secondary" onClick={() => void signOut()} type="button">
        Sign out
      </button>
    );
  }

  return (
    <button className="button" onClick={() => void signIn("google")} type="button">
      Sign in with Google
    </button>
  );
}
