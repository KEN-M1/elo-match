import type { League, LeagueMember, Match, RatingHistoryEntry, User } from "@rankkit/types";

import { api } from "./api";

export type DemoState = {
  owner?: User;
  opponent?: User;
  league?: League;
  members: LeagueMember[];
  match?: Match;
  ownerHistory: RatingHistoryEntry[];
  opponentHistory: RatingHistoryEntry[];
};

export type LocalDemoInput = {
  ownerEmail: string;
  opponentEmail: string;
  leagueName: string;
};

export type LocalDemoOptions = {
  client?: LocalDemoApi;
  slugSuffix?: string;
  onStatus?: (status: string) => void;
};

export type LocalDemoApi = {
  auth: {
    sync: (body: { email: string; name?: string; image?: string }) => Promise<User>;
  };
  leagues: {
    create: (body: {
      owner_id: string;
      name: string;
      slug: string;
      description?: string;
      is_public?: boolean;
    }) => Promise<League>;
    leaderboard: (leagueId: string) => Promise<LeagueMember[]>;
  };
  invites: {
    create: (leagueId: string, adminId: string) => Promise<{ token: string }>;
    accept: (token: string, userId: string) => Promise<LeagueMember>;
  };
  matches: {
    log: (
      leagueId: string,
      body: { reported_by_id: string; winner_id: string; loser_id: string },
    ) => Promise<Match>;
    confirm: (leagueId: string, matchId: string, actorId: string) => Promise<Match>;
  };
  ratings: {
    history: (leagueId: string, userId: string) => Promise<RatingHistoryEntry[]>;
  };
};

export const emptyDemoState: DemoState = {
  members: [],
  ownerHistory: [],
  opponentHistory: [],
};

export async function runLocalDemo(
  input: LocalDemoInput,
  options: LocalDemoOptions = {},
): Promise<DemoState> {
  const client = options.client ?? api;
  const status = options.onStatus ?? (() => undefined);
  const slug = buildDemoSlug(input.leagueName, options.slugSuffix ?? Date.now().toString(36));

  status("Syncing demo users...");
  const owner = await client.auth.sync({ email: input.ownerEmail, name: "Owner" });
  const opponent = await client.auth.sync({ email: input.opponentEmail, name: "Opponent" });

  status("Creating league...");
  const league = await client.leagues.create({
    owner_id: owner.id,
    name: input.leagueName,
    slug,
    is_public: true,
  });

  status("Creating invite and accepting as opponent...");
  const invite = await client.invites.create(league.id, owner.id);
  await client.invites.accept(invite.token, opponent.id);

  status("Logging match...");
  const match = await client.matches.log(league.id, {
    reported_by_id: owner.id,
    winner_id: owner.id,
    loser_id: opponent.id,
  });

  status("Confirming match as opponent...");
  const confirmed = await client.matches.confirm(league.id, match.id, opponent.id);
  const members = await client.leagues.leaderboard(league.id);
  const ownerHistory = await client.ratings.history(league.id, owner.id);
  const opponentHistory = await client.ratings.history(league.id, opponent.id);

  return {
    owner,
    opponent,
    league,
    members,
    match: confirmed,
    ownerHistory,
    opponentHistory,
  };
}

export function buildDemoSlug(value: string, suffix: string) {
  return `${slugify(value)}-${suffix}`;
}

function slugify(value: string) {
  return (
    value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "rankkit"
  );
}
