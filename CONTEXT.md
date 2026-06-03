# RankKit Context

## Domain Glossary

- **League**: A competitive group with members, matches, rating settings, and a leaderboard.
- **League Owner**: The user who creates a league and receives admin permissions.
- **League Member**: A user who has joined a league and can appear on the leaderboard.
- **Invite**: A tokenized join link for adding a user to a league.
- **Match**: A reported competitive result between two league members.
- **Match Participant**: A user involved in a match, including their rating before and after confirmation.
- **Pending Match**: A reported match waiting for opponent confirmation.
- **Disputed Match**: A reported match challenged by the opponent.
- **Confirmed Match**: A match that has been accepted and applied to ratings.
- **Leaderboard**: The ordered list of league members by rating.
- **Rating History**: The append-only record of rating values after confirmed matches.
- **Public League Page**: A read-only leaderboard reachable by slug without auth when public.
- **Store Snapshot**: The persisted local JSON representation of RankKit users, leagues, members, invites, matches, and rating history.
- **League Workspace**: The authenticated league management surface that loads league state and coordinates invites, local actor selection, match logging, confirmations, disputes, and rating history.
- **Authenticated Actor**: The current browser user, resolved from Google OAuth or the local demo fallback, who performs league and match actions.
- **RankKit Client**: The web module that converts backend transport responses into RankKit domain values for screens and workflows.
- **Postgres Schema**: The future database table shape for RankKit users, leagues, members, invites, matches, and rating history; separate from the local Store Snapshot until a real adapter is implemented.

## Architectural Vocabulary

Architecture reviews should use: module, interface, implementation, depth, seam, adapter, leverage, and locality.
