import { LeagueClient } from "./league-client";

export default function LeaguePage({ params }: { params: { id: string } }) {
  return <LeagueClient leagueId={params.id} />;
}
