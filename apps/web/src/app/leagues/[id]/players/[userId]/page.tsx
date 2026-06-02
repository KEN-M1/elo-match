import { PlayerClient } from "./player-client";

export default function PlayerPage({ params }: { params: { id: string; userId: string } }) {
  return <PlayerClient leagueId={params.id} userId={params.userId} />;
}
