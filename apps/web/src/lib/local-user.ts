import type { User } from "@rankkit/types";

const STORAGE_KEY = "rankkit.localUser";

export function getLocalUser(): User | null {
  if (typeof window === "undefined") return null;
  const value = window.localStorage.getItem(STORAGE_KEY);
  if (!value) return null;

  try {
    return JSON.parse(value) as User;
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

export function setLocalUser(user: User) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
}
