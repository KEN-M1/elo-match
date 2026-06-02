"use client";

import Link from "next/link";
import { useState } from "react";

import { api } from "../../../lib/api";
import { setLocalUser } from "../../../lib/local-user";

export function InviteClient({ token }: { token: string }) {
  const [email, setEmail] = useState("player@example.com");
  const [status, setStatus] = useState("Accept this RankKit invite with a local demo user.");
  const [error, setError] = useState<string | null>(null);
  const [leagueId, setLeagueId] = useState<string | null>(null);

  async function acceptInvite() {
    setError(null);
    setStatus("Syncing local user...");

    try {
      const user = (await api.auth.sync({ email, name: email.split("@")[0] || "Player" })).data;
      setLocalUser(user);
      const member = (await api.invites.accept(token, user.id)).data;
      setLeagueId(member.league_id);
      setStatus("Invite accepted. You can open the league workspace.");
    } catch (inviteError) {
      setError(inviteError instanceof Error ? inviteError.message : "Could not accept invite.");
      setStatus("Invite stopped.");
    }
  }

  return (
    <main className="shell">
      <div className="topbar">
        <div>
          <div className="brand">Accept invite</div>
          <p className="muted">Token {token}</p>
        </div>
        <Link className="button secondary" href="/">
          Home
        </Link>
      </div>
      <section className="panel form">
        <label className="field">
          Your email
          <input value={email} onChange={(event) => setEmail(event.target.value)} />
        </label>
        <button className="button" onClick={acceptInvite} type="button">
          Accept invite
        </button>
        {leagueId ? (
          <Link className="button secondary" href={`/leagues/${leagueId}`}>
            Open league
          </Link>
        ) : null}
        <p className={`status ${error ? "error" : ""}`}>{error ?? status}</p>
      </section>
    </main>
  );
}
