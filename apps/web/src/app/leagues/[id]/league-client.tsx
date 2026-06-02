"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { League, Match, MemberSummary, RatingHistoryEntry, User } from "@rankkit/types";

import { api } from "../../../lib/api";
import { getLocalUser, setLocalUser } from "../../../lib/local-user";

export function LeagueClient({ leagueId }: { leagueId: string }) {
  const [league, setLeague] = useState<League | null>(null);
  const [members, setMembers] = useState<MemberSummary[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [history, setHistory] = useState<RatingHistoryEntry[]>([]);
  const [localUser, setUser] = useState<User | null>(null);
  const [inviteToken, setInviteToken] = useState<string | null>(null);
  const [newMemberEmail, setNewMemberEmail] = useState("opponent@example.com");
  const [winnerId, setWinnerId] = useState("");
  const [loserId, setLoserId] = useState("");
  const [status, setStatus] = useState("Loading league...");
  const [error, setError] = useState<string | null>(null);

  const pendingMatches = useMemo(
    () => matches.filter((match) => match.status === "PENDING" || match.status === "DISPUTED"),
    [matches],
  );
  const localMembership = useMemo(
    () => members.find((member) => member.user_id === localUser?.id),
    [members, localUser],
  );
  const canResolveDisputes = localMembership?.role === "admin";

  useEffect(() => {
    const user = getLocalUser();
    setUser(user);
    void refresh(user);
  }, [leagueId]);

  async function refresh(user = localUser) {
    setError(null);
    try {
      const [leagueResponse, leaderboardResponse, matchesResponse] = await Promise.all([
        api.leagues.get(leagueId),
        api.leagues.members(leagueId),
        api.matches.list(leagueId),
      ]);
      setLeague(leagueResponse.data);
      setMembers(leaderboardResponse.data);
      setMatches(matchesResponse.data);
      setWinnerId((current) => current || leaderboardResponse.data[0]?.user_id || "");
      setLoserId((current) => current || leaderboardResponse.data[1]?.user_id || "");

      const historyUserId = user?.id ?? leaderboardResponse.data[0]?.user_id;
      if (historyUserId) {
        setHistory((await api.ratings.history(leagueId, historyUserId)).data);
      }
      setStatus("League loaded.");
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Could not load league.");
      setStatus("Load failed.");
    }
  }

  async function inviteAndAcceptMember() {
    if (!localUser) {
      setError("Create a league first so the local owner is known.");
      return;
    }

    setError(null);
    setStatus("Creating invite...");
    try {
      const invite = (await api.invites.create(leagueId, localUser.id)).data;
      setInviteToken(invite.token);
      const memberUser = (
        await api.auth.sync({ email: newMemberEmail, name: newMemberEmail.split("@")[0] })
      ).data;
      await api.invites.accept(invite.token, memberUser.id);
      setStatus("Invite accepted and member added.");
      await refresh();
    } catch (inviteError) {
      setError(inviteError instanceof Error ? inviteError.message : "Could not add member.");
      setStatus("Invite stopped.");
    }
  }

  async function claimAsLocalUser(member: MemberSummary) {
    const user = await api.auth.sync({
      email: member.email,
      name: member.name ?? member.email,
    });
    const claimed = { ...user.data, id: member.user_id };
    setLocalUser(claimed);
    setUser(claimed);
    setStatus("Local actor changed for browser actions.");
    await refresh(claimed);
  }

  async function logMatch() {
    if (!localUser) {
      setError("Create a league first so the local reporter is known.");
      return;
    }
    setError(null);
    setStatus("Logging match...");
    try {
      await api.matches.log(leagueId, {
        reported_by_id: localUser.id,
        winner_id: winnerId,
        loser_id: loserId,
      });
      setStatus("Match logged. Ratings are unchanged until confirmation.");
      await refresh();
    } catch (matchError) {
      setError(matchError instanceof Error ? matchError.message : "Could not log match.");
      setStatus("Match logging stopped.");
    }
  }

  async function confirmMatch(match: Match) {
    const actorId = match.reported_by_id === match.winner_id ? match.loser_id : match.winner_id;
    await mutateMatch(() => api.matches.confirm(leagueId, match.id, actorId), "Match confirmed.");
  }

  async function confirmMatchAsAdmin(match: Match) {
    if (!localUser) {
      setError("Choose an admin local actor before resolving a dispute.");
      return;
    }
    await mutateMatch(
      () => api.matches.confirm(leagueId, match.id, localUser.id),
      "Dispute resolved as confirmed.",
    );
  }

  async function disputeMatch(match: Match) {
    const actorId = match.reported_by_id === match.winner_id ? match.loser_id : match.winner_id;
    await mutateMatch(
      () => api.matches.dispute(leagueId, match.id, actorId, "Disputed from local demo UI."),
      "Match disputed.",
    );
  }

  async function rejectMatch(match: Match) {
    if (!localUser) {
      setError("Choose an admin local actor before resolving a dispute.");
      return;
    }
    await mutateMatch(() => api.matches.reject(leagueId, match.id, localUser.id), "Dispute rejected.");
  }

  async function mutateMatch(action: () => Promise<unknown>, success: string) {
    setError(null);
    try {
      await action();
      setStatus(success);
      await refresh();
    } catch (matchError) {
      setError(matchError instanceof Error ? matchError.message : "Match action failed.");
    }
  }

  function labelFor(userId: string) {
    const member = members.find((candidate) => candidate.user_id === userId);
    const label = member?.name || member?.email || userId;
    return localUser?.id === userId ? `${label} (local)` : label;
  }

  return (
    <main className="shell">
      <div className="topbar">
        <div>
          <div className="brand">{league?.name ?? `League ${leagueId}`}</div>
          <p className="muted">Leaderboard, invites, matches, and rating history.</p>
        </div>
        <div className="actions">
          <Link className="button secondary" href="/leagues/new">
            New league
          </Link>
          {league ? (
            <Link className="button secondary" href={`/l/${league.slug}`}>
              Public page
            </Link>
          ) : null}
        </div>
      </div>

      <section className="grid">
        <article className="panel">
          <h2>Leaderboard</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Player</th>
                <th>Rating</th>
                <th>Record</th>
                <th>Actor</th>
              </tr>
            </thead>
            <tbody>
              {members.map((member) => (
                <tr key={member.user_id}>
                  <td>
                    <Link className="inline-link" href={`/leagues/${leagueId}/players/${member.user_id}`}>
                      {labelFor(member.user_id)}
                    </Link>
                  </td>
                  <td>{member.rating}</td>
                  <td>
                    {member.wins}-{member.losses}
                  </td>
                  <td>
                    <button className="link-button" onClick={() => void claimAsLocalUser(member)}>
                      Use
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>

        <article className="panel form">
          <h2>Add member</h2>
          <label className="field">
            Member email
            <input value={newMemberEmail} onChange={(event) => setNewMemberEmail(event.target.value)} />
          </label>
          <button className="button" onClick={inviteAndAcceptMember} type="button">
            Create invite and accept
          </button>
          {inviteToken ? (
            <p className="muted">
              Last invite:{" "}
              <Link className="inline-link" href={`/invites/${inviteToken}`}>
                /invites/{inviteToken}
              </Link>
            </p>
          ) : null}
        </article>
      </section>

      <section className="grid">
        <article className="panel form">
          <h2>Log match</h2>
          <label className="field">
            Winner
            <select value={winnerId} onChange={(event) => setWinnerId(event.target.value)}>
              {members.map((member) => (
                <option key={member.user_id} value={member.user_id}>
                  {labelFor(member.user_id)}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Loser
            <select value={loserId} onChange={(event) => setLoserId(event.target.value)}>
              {members.map((member) => (
                <option key={member.user_id} value={member.user_id}>
                  {labelFor(member.user_id)}
                </option>
              ))}
            </select>
          </label>
          <button className="button" disabled={members.length < 2} onClick={logMatch} type="button">
            Log pending match
          </button>
        </article>

        <article className="panel">
          <h2>Pending matches</h2>
          <div className="stack">
            {pendingMatches.length === 0 ? (
              <p className="muted">No pending or disputed matches.</p>
            ) : (
              pendingMatches.map((match) => (
                <div className="mini-card" key={match.id}>
                  <strong>{match.status}</strong>
                  <p className="muted">
                    Winner {labelFor(match.winner_id)} over {labelFor(match.loser_id)}
                  </p>
                  <div className="actions">
                    {match.status === "PENDING" ? (
                      <>
                        <button className="button" onClick={() => void confirmMatch(match)} type="button">
                          Confirm as opponent
                        </button>
                        <button
                          className="button secondary"
                          onClick={() => void disputeMatch(match)}
                          type="button"
                        >
                          Dispute
                        </button>
                      </>
                    ) : null}
                    {match.status === "DISPUTED" && canResolveDisputes ? (
                      <>
                        <button className="button" onClick={() => void confirmMatchAsAdmin(match)} type="button">
                          Confirm as admin
                        </button>
                        <button
                          className="button secondary"
                          onClick={() => void rejectMatch(match)}
                          type="button"
                        >
                          Reject dispute
                        </button>
                      </>
                    ) : null}
                  </div>
                </div>
              ))
            )}
          </div>
        </article>
      </section>

      <section className="grid">
        <article className="panel">
          <h2>Recent matches</h2>
          <div className="stack">
            {matches.length === 0 ? (
              <p className="muted">No matches logged yet.</p>
            ) : (
              matches.map((match) => (
                <div className="mini-card" key={match.id}>
                  <strong>{match.status}</strong>
                  <p className="muted">
                    {labelFor(match.winner_id)} defeated {labelFor(match.loser_id)}
                  </p>
                </div>
              ))
            )}
          </div>
        </article>

        <article className="panel">
          <h2>Rating history</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Rating</th>
                <th>Match</th>
              </tr>
            </thead>
            <tbody>
              {history.map((entry, index) => (
                <tr key={`${entry.user_id}-${entry.match_id ?? "initial"}-${index}`}>
                  <td>{entry.rating}</td>
                  <td>{entry.match_id ?? "Initial"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>
      </section>

      <p className={`status ${error ? "error" : ""}`}>{error ?? status}</p>
    </main>
  );
}
