"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { League, LeagueMember, Match, RatingHistoryEntry, User } from "@rankkit/types";

import { api } from "../../lib/api";

type DemoState = {
  owner?: User;
  opponent?: User;
  league?: League;
  members: LeagueMember[];
  match?: Match;
  ownerHistory: RatingHistoryEntry[];
  opponentHistory: RatingHistoryEntry[];
};

const initialState: DemoState = {
  members: [],
  ownerHistory: [],
  opponentHistory: [],
};

export function DemoClient() {
  const [ownerEmail, setOwnerEmail] = useState("owner@example.com");
  const [opponentEmail, setOpponentEmail] = useState("opponent@example.com");
  const [leagueName, setLeagueName] = useState("Friday Ladder");
  const [state, setState] = useState<DemoState>(initialState);
  const [status, setStatus] = useState("Ready to run the local MVP flow.");
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const memberLabels = useMemo(() => {
    return new Map([
      [state.owner?.id, state.owner?.name ?? state.owner?.email],
      [state.opponent?.id, state.opponent?.name ?? state.opponent?.email],
    ]);
  }, [state.owner, state.opponent]);

  async function runDemo() {
    setIsRunning(true);
    setError(null);
    setStatus("Syncing demo users...");

    try {
      const slug = `${slugify(leagueName)}-${Date.now().toString(36)}`;
      const owner = await api.auth.sync({ email: ownerEmail, name: "Owner" });
      const opponent = await api.auth.sync({ email: opponentEmail, name: "Opponent" });

      setStatus("Creating league...");
      const league = await api.leagues.create({
        owner_id: owner.id,
        name: leagueName,
        slug,
        is_public: true,
      });

      setStatus("Creating invite and accepting as opponent...");
      const invite = await api.invites.create(league.id, owner.id);
      await api.invites.accept(invite.token, opponent.id);

      setStatus("Logging match...");
      const match = await api.matches.log(league.id, {
        reported_by_id: owner.id,
        winner_id: owner.id,
        loser_id: opponent.id,
      });

      setStatus("Confirming match as opponent...");
      const confirmed = await api.matches.confirm(league.id, match.id, opponent.id);
      const members = await api.leagues.leaderboard(league.id);
      const ownerHistory = await api.ratings.history(league.id, owner.id);
      const opponentHistory = await api.ratings.history(league.id, opponent.id);

      setState({
        owner,
        opponent,
        league,
        members,
        match: confirmed,
        ownerHistory,
        opponentHistory,
      });
      setStatus("Demo complete. Ratings moved only after opponent confirmation.");
    } catch (demoError) {
      setError(demoError instanceof Error ? demoError.message : "Demo failed.");
      setStatus("Demo stopped.");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <main className="shell">
      <nav className="topbar">
        <div>
          <div className="brand">RankKit Demo</div>
          <p className="muted">Create, invite, log, confirm, and refresh the leaderboard.</p>
        </div>
        <div className="actions">
          <Link className="button secondary" href="/">
            Home
          </Link>
          {state.league ? (
            <Link className="button secondary" href={`/l/${state.league.slug}`}>
              Public page
            </Link>
          ) : null}
        </div>
      </nav>

      <section className="grid">
        <form className="panel form">
          <label className="field">
            Owner email
            <input value={ownerEmail} onChange={(event) => setOwnerEmail(event.target.value)} />
          </label>
          <label className="field">
            Opponent email
            <input value={opponentEmail} onChange={(event) => setOpponentEmail(event.target.value)} />
          </label>
          <label className="field">
            League name
            <input value={leagueName} onChange={(event) => setLeagueName(event.target.value)} />
          </label>
          <button className="button" disabled={isRunning} onClick={runDemo} type="button">
            {isRunning ? "Running..." : "Run full MVP flow"}
          </button>
          <p className={`status ${error ? "error" : ""}`}>{error ?? status}</p>
        </form>

        <article className="panel stack">
          <div>
            <h2>Match state</h2>
            <p className="muted">{state.match?.status ?? "No match logged yet."}</p>
          </div>
          <div>
            <h2>League</h2>
            <p className="muted">
              {state.league ? `${state.league.name} / ${state.league.slug}` : "No league yet."}
            </p>
          </div>
        </article>
      </section>

      <section className="panel">
        <h2>Leaderboard</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Player</th>
              <th>Rating</th>
              <th>Record</th>
            </tr>
          </thead>
          <tbody>
            {state.members.length === 0 ? (
              <tr>
                <td colSpan={3}>Run the demo to populate standings.</td>
              </tr>
            ) : (
              state.members.map((member) => (
                <tr key={member.user_id}>
                  <td>{memberLabels.get(member.user_id) ?? member.user_id}</td>
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

      <section className="grid">
        <HistoryPanel label="Owner rating history" rows={state.ownerHistory} />
        <HistoryPanel label="Opponent rating history" rows={state.opponentHistory} />
      </section>
    </main>
  );
}

function HistoryPanel({ label, rows }: { label: string; rows: RatingHistoryEntry[] }) {
  return (
    <article className="panel">
      <h2>{label}</h2>
      <table className="table">
        <thead>
          <tr>
            <th>Rating</th>
            <th>Match</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={2}>No entries yet.</td>
            </tr>
          ) : (
            rows.map((row, index) => (
              <tr key={`${row.user_id}-${row.match_id ?? "initial"}-${index}`}>
                <td>{row.rating}</td>
                <td>{row.match_id ?? "Initial"}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </article>
  );
}

function slugify(value: string) {
  return (
    value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "rankkit"
  );
}
