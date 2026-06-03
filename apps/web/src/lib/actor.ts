import type { MemberSummary, User } from "@rankkit/types";

import { api } from "./api";
import { getLocalUser, setLocalUser } from "./local-user";

type ActorProfile = {
  email: string;
  name?: string | null;
  image?: string | null;
};

type SessionActorProfile = {
  accessToken?: string;
  user?: {
    email?: string | null;
    name?: string | null;
    image?: string | null;
  } | null;
};

export function getStoredActor(): User | null {
  return getLocalUser();
}

export async function syncLocalActor(profile: ActorProfile, fallbackName = "Player"): Promise<User> {
  const user = await api.auth.sync({
    email: profile.email,
    name: profile.name ?? nameFromEmail(profile.email, fallbackName),
    image: profile.image ?? undefined,
  });
  setLocalUser(user);
  return user;
}

export async function syncSessionActor(session: SessionActorProfile): Promise<User | null> {
  if (!session.user?.email) return null;

  const response = session.accessToken
    ? await api.auth.me(session.accessToken)
    : await api.auth.sync({
        email: session.user.email,
        name: session.user.name ?? undefined,
        image: session.user.image ?? undefined,
      });

  setLocalUser(response);
  return response;
}

export async function claimMemberAsActor(member: MemberSummary): Promise<User> {
  const synced = await syncLocalActor({
    email: member.email,
    name: member.name ?? member.email,
  });
  const claimed = { ...synced, id: member.user_id };
  setLocalUser(claimed);
  return claimed;
}

function nameFromEmail(email: string, fallbackName: string) {
  return email.split("@")[0] || fallbackName;
}
