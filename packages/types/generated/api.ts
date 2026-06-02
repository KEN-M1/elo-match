export type User = {
  id: string;
  email: string;
  name?: string | null;
  image?: string | null;
};

export type League = {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  description?: string | null;
  is_public: boolean;
  default_k: number;
  initial_rating: number;
  rating_floor: number;
};

export type LeagueMember = {
  league_id: string;
  user_id: string;
  role: "admin" | "member";
  rating: number;
  wins: number;
  losses: number;
  joined_at: string;
};

export type MemberSummary = LeagueMember & {
  email: string;
  name?: string | null;
};

export type Invite = {
  token: string;
  league_id: string;
  created_by_id: string;
  accepted_by_id?: string | null;
  accepted_at?: string | null;
};

export type MatchStatus = "PENDING" | "DISPUTED" | "COMPLETED" | "REJECTED";

export type Match = {
  id: string;
  league_id: string;
  winner_id: string;
  loser_id: string;
  reported_by_id: string;
  status: MatchStatus;
  confirmed_by_id?: string | null;
  disputed_by_id?: string | null;
  dispute_note?: string | null;
};

export type RatingHistoryEntry = {
  user_id: string;
  league_id: string;
  match_id?: string | null;
  rating: number;
  recorded_at: string;
};

export type ApiResponse<T> = {
  data: T;
};

export type LocalUser = User;
