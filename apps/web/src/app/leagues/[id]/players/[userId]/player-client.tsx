"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { League, MemberSummary, RatingHistoryEntry } from "@rankkit/types";

import { api } from "../../../../../lib/api";

export function PlayerClient({ leagueId, userId }: { leagueId: string; userId: string }) {
  const [league, setLeague] = useState<League | null>(null);
  const [member, setMember] = useState<MemberSummary | null>(null);
  const [history, setHistory] = useState<RatingHistoryEntry[]>([]);
  const [status, setStatus] = useState("Loading player...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    Promise.all([
      api.leagues.get(leagueId),
      api.leagues.members(leagueId),
      api.ratings.history(leagueId, userId),
    ])
      .then(([leagueResponse, membersResponse, historyResponse]) => {
        if (!isMounted) return;
        setLeague(leagueResponse);
        setMember(
          membersResponse.find((candidate) => candidate.user_id === userId) ?? null,
        );
        setHistory(historyResponse);
        setStatus("Player loaded.");
      })
      .catch((loadError) => {
        if (!isMounted) return;
        setError(loadError instanceof Error ? loadError.message : "Could not load player.");
        setStatus("Load failed.");
      });

    return () => {
      isMounted = false;
    };
  }, [leagueId, userId]);

  const displayName = member?.name || member?.email || userId;
  const currentRating = history.at(-1)?.rating ?? member?.rating ?? 1000;
  const ratingDelta = useMemo(() => {
    if (history.length < 2) return 0;
    return Number((history.at(-1)!.rating - history[0].rating).toFixed(2));
  }, [history]);

  return (
    <main className="shell">
      <div className="topbar">
        <div>
          <div className="brand">{displayName}</div>
          <p className="muted">{league?.name ?? leagueId}</p>
        </div>
        <div className="actions">
          <Link className="button secondary" href={`/leagues/${leagueId}`}>
            League
          </Link>
          {league ? (
            <Link className="button secondary" href={`/l/${league.slug}`}>
              Public page
            </Link>
          ) : null}
        </div>
      </div>

      <section className="grid">
        <article className="panel stat-panel">
          <span className="muted">Current rating</span>
          <strong>{currentRating}</strong>
        </article>
        <article className="panel stat-panel">
          <span className="muted">Record</span>
          <strong>
            {member?.wins ?? 0}-{member?.losses ?? 0}
          </strong>
        </article>
        <article className="panel stat-panel">
          <span className="muted">Net movement</span>
          <strong>{ratingDelta >= 0 ? `+${ratingDelta}` : ratingDelta}</strong>
        </article>
      </section>

      <section className="grid">
        <article className="panel">
          <h2>Rating chart</h2>
          <RatingChart history={history} />
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
              {history.length === 0 ? (
                <tr>
                  <td colSpan={2}>No rating history yet.</td>
                </tr>
              ) : (
                history.map((entry, index) => (
                  <tr key={`${entry.user_id}-${entry.match_id ?? "initial"}-${index}`}>
                    <td>{entry.rating}</td>
                    <td>{entry.match_id ?? "Initial"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </article>
      </section>

      <p className={`status ${error ? "error" : ""}`}>{error ?? status}</p>
    </main>
  );
}

function RatingChart({ history }: { history: RatingHistoryEntry[] }) {
  if (history.length === 0) {
    return <p className="muted">No points to chart yet.</p>;
  }

  const width = 640;
  const height = 220;
  const padding = 28;
  const values = history.map((entry) => entry.rating);
  const min = Math.min(900, ...values);
  const max = Math.max(1100, ...values);
  const spread = Math.max(1, max - min);
  const points = values.map((rating, index) => {
    const x =
      history.length === 1
        ? width / 2
        : padding + (index / (history.length - 1)) * (width - padding * 2);
    const y = height - padding - ((rating - min) / spread) * (height - padding * 2);
    return { x, y, rating };
  });
  const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
  const baselineY = height - padding - ((1000 - min) / spread) * (height - padding * 2);

  return (
    <svg className="rating-chart" role="img" viewBox={`0 0 ${width} ${height}`}>
      <line className="chart-baseline" x1={padding} x2={width - padding} y1={baselineY} y2={baselineY} />
      <path className="chart-line" d={path} />
      {points.map((point, index) => (
        <g key={`${point.x}-${point.y}`}>
          <circle className="chart-point" cx={point.x} cy={point.y} r="4" />
          {index === points.length - 1 ? (
            <text className="chart-label" x={point.x - 18} y={point.y - 10}>
              {point.rating}
            </text>
          ) : null}
        </g>
      ))}
      <text className="chart-label" x={padding} y={baselineY - 8}>
        1000
      </text>
    </svg>
  );
}
