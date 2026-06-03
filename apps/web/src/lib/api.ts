import type {
  ApiResponse,
  Invite,
  League,
  LeagueMember,
  MemberSummary,
  Match,
  RatingHistoryEntry,
  User,
} from "@rankkit/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`RankKit API ${response.status}: ${detail}`);
  }

  const payload = (await response.json()) as ApiResponse<T>;
  return payload.data;
}

export const api = {
  auth: {
    me: (accessToken: string) =>
      request<User>("/v1/auth/me", {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }),
    sync: (body: { email: string; name?: string; image?: string }) =>
      request<User>("/v1/auth/sync", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  },
  leagues: {
    list: (userId?: string) => {
      const query = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
      return request<League[]>(`/v1/leagues${query}`);
    },
    get: (leagueId: string) => request<League>(`/v1/leagues/${leagueId}`),
    members: (leagueId: string) =>
      request<MemberSummary[]>(`/v1/leagues/${leagueId}/members`),
    create: (body: {
      owner_id: string;
      name: string;
      slug: string;
      description?: string;
      is_public?: boolean;
    }) =>
      request<League>("/v1/leagues", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    leaderboard: (leagueId: string) =>
      request<LeagueMember[]>(`/v1/leagues/${leagueId}/leaderboard`),
    publicLeaderboard: (slug: string) =>
      request<[League, MemberSummary[]]>(`/v1/public/leagues/${slug}`),
  },
  invites: {
    create: (leagueId: string, adminId: string) =>
      request<Invite>(`/v1/leagues/${leagueId}/invites`, {
        method: "POST",
        body: JSON.stringify({ admin_id: adminId }),
      }),
    accept: (token: string, userId: string) =>
      request<LeagueMember>(`/v1/invites/${token}/accept`, {
        method: "POST",
        body: JSON.stringify({ user_id: userId }),
      }),
  },
  matches: {
    list: (leagueId: string) =>
      request<Match[]>(`/v1/leagues/${leagueId}/matches`),
    log: (
      leagueId: string,
      body: { reported_by_id: string; winner_id: string; loser_id: string },
    ) =>
      request<Match>(`/v1/leagues/${leagueId}/matches`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    confirm: (leagueId: string, matchId: string, actorId: string) =>
      request<Match>(`/v1/leagues/${leagueId}/matches/${matchId}/confirm`, {
        method: "POST",
        body: JSON.stringify({ actor_id: actorId }),
      }),
    dispute: (leagueId: string, matchId: string, actorId: string, note?: string) =>
      request<Match>(`/v1/leagues/${leagueId}/matches/${matchId}/dispute`, {
        method: "POST",
        body: JSON.stringify({ actor_id: actorId, note }),
      }),
    reject: (leagueId: string, matchId: string, actorId: string) =>
      request<Match>(`/v1/leagues/${leagueId}/matches/${matchId}/reject`, {
        method: "POST",
        body: JSON.stringify({ actor_id: actorId }),
      }),
  },
  ratings: {
    history: (leagueId: string, userId: string) =>
      request<RatingHistoryEntry[]>(
        `/v1/leagues/${leagueId}/players/${userId}/rating-history`,
      ),
  },
};
