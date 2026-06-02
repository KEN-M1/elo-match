# Confirm Match and Update Elo Ratings

## What to build

Allow the opponent to confirm a pending match and update both players' Elo ratings atomically.

## Acceptance criteria

- [ ] Only the opponent or an admin can confirm a pending match.
- [ ] Confirming applies Elo with initial `1000`, K `32`, and floor `100`.
- [ ] Rating history is appended for both participants.
- [ ] The leaderboard reflects the new ratings.

## Blocked by

005-log-1v1-match.
