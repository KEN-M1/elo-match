import Link from "next/link";

export default function HomePage() {
  return (
    <main className="shell">
      <nav className="topbar">
        <div className="brand">RankKit</div>
        <div className="actions">
          <Link className="button secondary" href="/dashboard">
            Dashboard
          </Link>
          <Link className="button" href="/demo">
            Run demo
          </Link>
        </div>
      </nav>
      <section className="grid">
        <article className="panel">
          <h1>1v1 Elo leagues</h1>
          <p className="muted">
            Create a league, invite members, log matches, confirm results, and share the
            leaderboard.
          </p>
        </article>
        <article className="panel">
          <h2>MVP loop</h2>
          <p className="muted">Ratings update only after opponent confirmation.</p>
        </article>
      </section>
    </main>
  );
}
