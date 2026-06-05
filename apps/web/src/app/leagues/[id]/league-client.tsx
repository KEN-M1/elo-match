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
              {workspace.memberRows.map((member) => (
                <tr key={member.userId}>
                  <td>
                    <Link className="inline-link" href={member.playerHref}>
                      {member.label}
                    </Link>
                  </td>
                  <td>{member.rating}</td>
                  <td>{member.record}</td>
                  <td>
                    <button className="link-button" onClick={() => void member.useAsActor()}>
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
              value={workspace.newMember.email}
              onChange={(event) => workspace.newMember.changeEmail(event.target.value)}
            />
          </label>
          <button className="button" onClick={workspace.newMember.submit} type="button">
            Create invite and accept
          </button>
          {workspace.newMember.inviteToken ? (
            <p className="muted">
              Last invite:{" "}
              <Link className="inline-link" href={`/invites/${workspace.newMember.inviteToken}`}>
                /invites/{workspace.newMember.inviteToken}
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
            <select
              value={workspace.matchForm.winnerId}
              onChange={(event) => workspace.matchForm.chooseWinner(event.target.value)}
            >
              {workspace.matchForm.winnerOptions.map((member) => (
                <option key={member.userId} value={member.userId}>
                  {member.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Loser
            <select
              value={workspace.matchForm.loserId}
              onChange={(event) => workspace.matchForm.chooseLoser(event.target.value)}
            >
              {workspace.matchForm.loserOptions.map((member) => (
                <option key={member.userId} value={member.userId}>
                  {member.label}
                </option>
              ))}
            </select>
          </label>
          <button
            className="button"
            disabled={!workspace.matchForm.canSubmit}
            onClick={workspace.matchForm.submit}
            type="button"
          >
            Log pending match
          </button>
        </article>

        <article className="panel">
          <h2>Pending matches</h2>
          <div className="stack">
            {workspace.pendingMatchCards.length === 0 ? (
              <p className="muted">No pending or disputed matches.</p>
            ) : (
              workspace.pendingMatchCards.map((match) => (
                <div className="mini-card" key={match.id}>
                  <strong>{match.status}</strong>
                  <p className="muted">{match.summary}</p>
                  <div className="actions">
                    {match.confirmAsOpponent ? (
                      <>
                        <button className="button" onClick={() => void match.confirmAsOpponent?.()} type="button">
                          Confirm as opponent
                        </button>
                        <button
                          className="button secondary"
                          onClick={() => void match.dispute?.()}
                          type="button"
                        >
                          Dispute
                        </button>
                      </>
                    ) : null}
                    {match.confirmAsAdmin ? (
                      <>
                        <button className="button" onClick={() => void match.confirmAsAdmin?.()} type="button">
                          Confirm as admin
                        </button>
                        <button
                          className="button secondary"
                          onClick={() => void match.reject?.()}
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
            {workspace.recentMatchCards.length === 0 ? (
              <p className="muted">No matches logged yet.</p>
            ) : (
              workspace.recentMatchCards.map((match) => (
                <div className="mini-card" key={match.id}>
                  <strong>{match.status}</strong>
                  <p className="muted">{match.summary}</p>
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
              {workspace.ratingHistoryRows.map((entry) => (
                <tr key={entry.key}>
                  <td>{entry.rating}</td>
                  <td>{entry.matchLabel}</td>
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
