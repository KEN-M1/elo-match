"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { api } from "../../../lib/api";
import { setLocalUser } from "../../../lib/local-user";

export function NewLeagueClient() {
  const router = useRouter();
  const [email, setEmail] = useState("owner@example.com");
  const [name, setName] = useState("Friday Ladder");
  const [slug, setSlug] = useState("friday-ladder");
  const [isPublic, setIsPublic] = useState(true);
  const [status, setStatus] = useState("Create a local MVP league.");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function createLeague() {
    setIsSubmitting(true);
    setError(null);
    setStatus("Syncing local user...");

    try {
      const user = (await api.auth.sync({ email, name: email.split("@")[0] || "Owner" })).data;
      setLocalUser(user);

      setStatus("Creating league...");
      const league = (
        await api.leagues.create({
          owner_id: user.id,
          name,
          slug: slugify(slug || name),
          is_public: isPublic,
        })
      ).data;

      router.push(`/leagues/${league.id}`);
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Could not create league.");
      setStatus("Creation stopped.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="shell">
      <div className="topbar">
        <div>
          <div className="brand">Create league</div>
          <p className="muted">MVP defaults: 1v1 Elo, initial 1000, K 32, rating floor 100.</p>
        </div>
        <Link className="button secondary" href="/dashboard">
          Dashboard
        </Link>
      </div>
      <form className="panel form">
        <label className="field">
          Your email
          <input value={email} onChange={(event) => setEmail(event.target.value)} />
        </label>
        <label className="field">
          League name
          <input value={name} onChange={(event) => setName(event.target.value)} />
        </label>
        <label className="field">
          Slug
          <input value={slug} onChange={(event) => setSlug(event.target.value)} />
        </label>
        <label className="check">
          <input
            checked={isPublic}
            onChange={(event) => setIsPublic(event.target.checked)}
            type="checkbox"
          />{" "}
          Public leaderboard
        </label>
        <button className="button" disabled={isSubmitting} onClick={createLeague} type="button">
          {isSubmitting ? "Creating..." : "Create league"}
        </button>
        <p className={`status ${error ? "error" : ""}`}>{error ?? status}</p>
      </form>
    </main>
  );
}

function slugify(value: string) {
  return (
    value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "rankkit"
  );
}
