"use client";

import { useEffect, useMemo, useState } from "react";
import type { League, Match, MemberSummary, RatingHistoryEntry, User } from "@rankkit/types";

import { api } from "../../../lib/api";
import { claimMemberAsActor, getStoredActor } from "../../../lib/actor";

export function useLeagueWorkspace(leagueId: string) {
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
    const user = getStoredActor();
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
      setLeague(leagueResponse);
      setMembers(leaderboardResponse);
      setMatches(matchesResponse);
      setWinnerId((current) => current || leaderboardResponse[0]?.user_id || "");
      setLoserId((current) => current || leaderboardResponse[1]?.user_id || "");

      const historyUserId = user?.id ?? leaderboardResponse[0]?.user_id;
      if (historyUserId) {
        setHistory(await api.ratings.history(leagueId, historyUserId));
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
      const invite = await api.invites.create(leagueId, localUser.id);
      setInviteToken(invite.token);
      const memberUser = await api.auth.sync({
        email: newMemberEmail,
        name: newMemberEmail.split("@")[0],
      });
      await api.invites.accept(invite.token, memberUser.id);
      setStatus("Invite accepted and member added.");
      await refresh();
    } catch (inviteError) {
      setError(inviteError instanceof Error ? inviteError.message : "Could not add member.");
      setStatus("Invite stopped.");
    }
  }

  async function claimAsLocalUser(member: MemberSummary) {
    const claimed = await claimMemberAsActor(member);
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

  const memberRows = useMemo(
    () =>
      members.map((member) => ({
        userId: member.user_id,
        label: labelFor(member.user_id),
        playerHref: `/leagues/${leagueId}/players/${member.user_id}`,
        rating: member.rating,
        record: `${member.wins}-${member.losses}`,
        useAsActor: () => claimAsLocalUser(member),
      })),
    [leagueId, localUser, members],
  );

  const matchOptions = useMemo(
    () =>
      members.map((member) => ({
        userId: member.user_id,
        label: labelFor(member.user_id),
      })),
    [localUser, members],
  );

  const matchForm = {
    canSubmit: members.length >= 2,
    chooseLoser: setLoserId,
    chooseWinner: setWinnerId,
    loserId,
    loserOptions: matchOptions,
    submit: logMatch,
    winnerId,
    winnerOptions: matchOptions,
  };

  const newMember = {
    changeEmail: setNewMemberEmail,
    email: newMemberEmail,
    inviteToken,
    submit: inviteAndAcceptMember,
  };

  const pendingMatchCards = useMemo(
    () =>
      pendingMatches.map((match) => ({
        id: match.id,
        status: match.status,
        summary: `Winner ${labelFor(match.winner_id)} over ${labelFor(match.loser_id)}`,
        confirmAsAdmin:
          match.status === "DISPUTED" && canResolveDisputes
            ? () => confirmMatchAsAdmin(match)
            : null,
        confirmAsOpponent: match.status === "PENDING" ? () => confirmMatch(match) : null,
        dispute: match.status === "PENDING" ? () => disputeMatch(match) : null,
        reject:
          match.status === "DISPUTED" && canResolveDisputes
            ? () => rejectMatch(match)
            : null,
      })),
    [canResolveDisputes, leagueId, localUser, members, pendingMatches],
  );

  const recentMatchCards = useMemo(
    () =>
      matches.map((match) => ({
        id: match.id,
        status: match.status,
        summary: `${labelFor(match.winner_id)} defeated ${labelFor(match.loser_id)}`,
      })),
    [localUser, matches, members],
  );

  const ratingHistoryRows = history.map((entry, index) => ({
    key: `${entry.user_id}-${entry.match_id ?? "initial"}-${index}`,
    matchLabel: entry.match_id ?? "Initial",
    rating: entry.rating,
  }));

  function labelFor(userId: string) {
    const member = members.find((candidate) => candidate.user_id === userId);
    const label = member?.name || member?.email || userId;
    return localUser?.id === userId ? `${label} (local)` : label;
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

  return {
    error,
    league,
    matchForm,
    memberRows,
    newMember,
    pendingMatchCards,
    ratingHistoryRows,
    recentMatchCards,
    status,
  };
}
