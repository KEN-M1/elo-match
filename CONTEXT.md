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

## Architectural Vocabulary

Architecture reviews should use: module, interface, implementation, depth, seam, adapter, leverage, and locality.
