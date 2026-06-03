"use client";

import { useEffect, useMemo, useState } from "react";
import type { League, MemberSummary } from "@rankkit/types";

import { api } from "../../../lib/api";

export function PublicLeagueClient({ slug }: { slug: string }) {
  const [league, setLeague] = useState<League | null>(null);
  const [members, setMembers] = useState<MemberSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    api.leagues
      .publicLeaderboard(slug)
      .then((response) => {
        if (!isMounted) return;
        setLeague(response[0]);
        setMembers(response[1]);
      })
      .catch((publicError) => {
        if (!isMounted) return;
        setError(publicError instanceof Error ? publicError.message : "Public leaderboard failed.");
      });

    return () => {
      isMounted = false;
    };
  }, [slug]);

  const title = useMemo(() => league?.name ?? slug, [league, slug]);

  return (
    <main className="shell">
      <div className="topbar">
        <div>
          <div className="brand">Public leaderboard</div>
          <p className="muted">/{slug}</p>
        </div>
      </div>
      <section className="panel">
        <h1>{title}</h1>
        {error ? <p className="status error">{error}</p> : null}
        <table className="table">
          <thead>
            <tr>
              <th>Player</th>
              <th>Rating</th>
              <th>Record</th>
            </tr>
          </thead>
          <tbody>
            {members.length === 0 ? (
              <tr>
                <td colSpan={3}>No public standings loaded yet.</td>
              </tr>
            ) : (
              members.map((member) => (
                <tr key={member.user_id}>
                  <td>{member.name || member.email}</td>
                  <td>{member.rating}</td>
                  <td>
                    {member.wins}-{member.losses}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </main>
  );
}
