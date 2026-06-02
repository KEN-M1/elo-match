import { PublicLeagueClient } from "./public-league-client";

export default function PublicLeaguePage({ params }: { params: { slug: string } }) {
  return <PublicLeagueClient slug={params.slug} />;
}
