"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { League, User } from "@rankkit/types";

import { api } from "../../lib/api";
import { getStoredActor, syncLocalActor } from "../../lib/actor";

export function DashboardClient() {
  const [email, setEmail] = useState("owner@example.com");
  const [user, setUser] = useState<User | null>(null);
  const [leagues, setLeagues] = useState<League[]>([]);
  const [status, setStatus] = useState("Sync a local user to see their leagues.");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const existingUser = getStoredActor();
    if (!existingUser) return;
    setUser(existingUser);
    setEmail(existingUser.email);
    void loadLeagues(existingUser);
  }, []);

  async function syncUser() {
    setError(null);
    setStatus("Syncing local user...");

    try {
      const synced = await syncLocalActor({ email }, "Owner");
      setUser(synced);
      await loadLeagues(synced);
    } catch (syncError) {
      setError(syncError instanceof Error ? syncError.message : "Could not sync local user.");
      setStatus("Sync failed.");
    }
  }

  async function loadLeagues(currentUser = user) {
    setError(null);

    try {
      const response = await api.leagues.list(currentUser?.id);
      setLeagues(response);
      setStatus(
        currentUser
          ? `Showing leagues for ${currentUser.email}.`
          : "Showing all locally persisted leagues.",
      );
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Could not load leagues.");
      setStatus("Load failed.");
    }
  }

  return (
    <main className="shell">
      <nav className="topbar">
        <div>
          <div className="brand">Dashboard</div>
          <p className="muted">Reopen persisted leagues and continue local match work.</p>
        </div>
        <div className="actions">
          <button className="button secondary" onClick={() => void loadLeagues(null)} type="button">
            Show all
          </button>
          <Link className="button" href="/leagues/new">
            New league
          </Link>
        </div>
      </nav>

      <section className="grid">
        <article className="panel form">
          <h2>Local actor</h2>
          <label className="field">
            Email
            <input value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <button className="button" onClick={syncUser} type="button">
            Sync and load leagues
          </button>
          <p className={`status ${error ? "error" : ""}`}>{error ?? status}</p>
        </article>

        <article className="panel scroll-panel">
          <h2>Leagues</h2>
          <div className="stack">
            {leagues.length === 0 ? (
              <p className="muted">No leagues found for this view.</p>
            ) : (
              leagues.map((league) => (
                <div className="mini-card" key={league.id}>
                  <strong>{league.name}</strong>
                  <p className="muted">/{league.slug}</p>
                  <div className="actions">
                    <Link className="button" href={`/leagues/${league.id}`}>
                      Open
                    </Link>
                    {league.is_public ? (
                      <Link className="button secondary" href={`/l/${league.slug}`}>
                        Public
                      </Link>
                    ) : null}
                  </div>
                </div>
              ))
            )}
          </div>
        </article>
      </section>
    </main>
  );
}
