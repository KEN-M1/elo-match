import Link from "next/link";

import { SignInButton } from "../auth/sign-in-button";

export default function SignInPage() {
  return (
    <main className="shell">
      <nav className="topbar">
        <div>
          <div className="brand">Sign in</div>
          <p className="muted">Use Google for the production auth shell, or keep using local demo flows.</p>
        </div>
        <Link className="button secondary" href="/">
          Home
        </Link>
      </nav>
      <section className="panel stack">
        <h1>RankKit account</h1>
        <p className="muted">
          Google OAuth requires `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `NEXTAUTH_SECRET`.
        </p>
        <div className="actions">
          <SignInButton />
          <Link className="button secondary" href="/demo">
            Local demo
          </Link>
        </div>
      </section>
    </main>
  );
}
