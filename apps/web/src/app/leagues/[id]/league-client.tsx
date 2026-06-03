"use client";

import Link from "next/link";

import { useLeagueWorkspace } from "./league-workspace";

export function LeagueClient({ leagueId }: { leagueId: string }) {
  const workspace = useLeagueWorkspace(leagueId);

  return (
    <main className="shell">
      <div className="topbar">
        <div>
          <div className="brand">{workspace.league?.name ?? `League ${leagueId}`}</div>
          <p className="muted">Leaderboard, invites, matches, and rating history.</p>
        </div>
        <div className="actions">
          <Link className="button secondary" href="/leagues/new">
            New league
          </Link>
          {workspace.league ? (
            <Link className="button secondary" href={`/l/${workspace.league.slug}`}>
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
              {workspace.members.map((member) => (
                <tr key={member.user_id}>
                  <td>
                    <Link className="inline-link" href={`/leagues/${leagueId}/players/${member.user_id}`}>
                      {workspace.labelFor(member.user_id)}
                    </Link>
                  </td>
                  <td>{member.rating}</td>
                  <td>
                    {member.wins}-{member.losses}
                  </td>
                  <td>
                    <button className="link-button" onClick={() => void workspace.claimAsLocalUser(member)}>
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
            <input
              value={workspace.newMemberEmail}
              onChange={(event) => workspace.setNewMemberEmail(event.target.value)}
            />
          </label>
          <button className="button" onClick={workspace.inviteAndAcceptMember} type="button">
            Create invite and accept
          </button>
          {workspace.inviteToken ? (
            <p className="muted">
              Last invite:{" "}
              <Link className="inline-link" href={`/invites/${workspace.inviteToken}`}>
                /invites/{workspace.inviteToken}
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
            <select value={workspace.winnerId} onChange={(event) => workspace.setWinnerId(event.target.value)}>
              {workspace.members.map((member) => (
                <option key={member.user_id} value={member.user_id}>
                  {workspace.labelFor(member.user_id)}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Loser
            <select value={workspace.loserId} onChange={(event) => workspace.setLoserId(event.target.value)}>
              {workspace.members.map((member) => (
                <option key={member.user_id} value={member.user_id}>
                  {workspace.labelFor(member.user_id)}
                </option>
              ))}
            </select>
          </label>
          <button className="button" disabled={workspace.members.length < 2} onClick={workspace.logMatch} type="button">
            Log pending match
          </button>
        </article>

        <article className="panel">
          <h2>Pending matches</h2>
          <div className="stack">
            {workspace.pendingMatches.length === 0 ? (
              <p className="muted">No pending or disputed matches.</p>
            ) : (
              workspace.pendingMatches.map((match) => (
                <div className="mini-card" key={match.id}>
                  <strong>{match.status}</strong>
                  <p className="muted">
                    Winner {workspace.labelFor(match.winner_id)} over {workspace.labelFor(match.loser_id)}
                  </p>
                  <div className="actions">
                    {match.status === "PENDING" ? (
                      <>
                        <button className="button" onClick={() => void workspace.confirmMatch(match)} type="button">
                          Confirm as opponent
                        </button>
                        <button
                          className="button secondary"
                          onClick={() => void workspace.disputeMatch(match)}
                          type="button"
                        >
                          Dispute
                        </button>
                      </>
                    ) : null}
                    {match.status === "DISPUTED" && workspace.canResolveDisputes ? (
                      <>
                        <button className="button" onClick={() => void workspace.confirmMatchAsAdmin(match)} type="button">
                          Confirm as admin
                        </button>
                        <button
                          className="button secondary"
                          onClick={() => void workspace.rejectMatch(match)}
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
            {workspace.matches.length === 0 ? (
              <p className="muted">No matches logged yet.</p>
            ) : (
              workspace.matches.map((match) => (
                <div className="mini-card" key={match.id}>
                  <strong>{match.status}</strong>
                  <p className="muted">
                    {workspace.labelFor(match.winner_id)} defeated {workspace.labelFor(match.loser_id)}
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
              {workspace.history.map((entry, index) => (
                <tr key={`${entry.user_id}-${entry.match_id ?? "initial"}-${index}`}>
                  <td>{entry.rating}</td>
                  <td>{entry.match_id ?? "Initial"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>
      </section>

      <p className={`status ${workspace.error ? "error" : ""}`}>{workspace.error ?? workspace.status}</p>
    </main>
  );
}
