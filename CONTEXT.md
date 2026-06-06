# RankKit Context

## Domain Glossary

- **League**: A competitive group with members, matches, rating settings, and a leaderboard.
- **League Owner**: The user who creates a league and receives admin permissions.
- **League Member**: A user who has joined a league and can appear on the leaderboard.
- **Membership Application**: The League Membership step that creates owner/member records, accepts invites, and creates initial Rating History entries.
- **Invite**: A tokenized join link for adding a user to a league.
- **Match**: A reported competitive result between two league members.
- **Match Lifecycle**: The state rules for logging, confirming, disputing, rejecting, and applying rating effects to a match.
- **Match Participant**: A user involved in a match, including their rating before and after confirmation.
- **Pending Match**: A reported match waiting for opponent confirmation.
- **Disputed Match**: A reported match challenged by the opponent.
- **Confirmed Match**: A match that has been accepted and applied to ratings.
- **Leaderboard**: The ordered list of league members by rating.
- **Leaderboard Projection**: The read-model step that ranks League Members and builds Member Summary rows for league and public views.
- **Rating Application**: The Match Lifecycle step that calculates Elo changes, updates participant records, and creates Rating History entries.
- **Rating History**: The append-only record of rating values after confirmed matches.
- **Public League Page**: A read-only leaderboard reachable by slug without auth when public.
- **Store Snapshot**: The persisted local JSON representation of RankKit users, leagues, members, invites, matches, and rating history.
- **League Workspace**: The authenticated league management module that loads league state and coordinates invites, local actor selection, match logging, confirmations, disputes, rating history, and display-ready rows/cards/forms for the league view.
- **Local Demo Flow**: The web module that runs the one-click MVP path by syncing demo users, creating a league, accepting an invite, logging and confirming a match, and loading standings/history.
- **Authenticated Actor**: The current browser user, resolved from Google OAuth or the local demo fallback, who performs league and match actions.
- **Auth Session**: The backend module that resolves the current User from either a verified bearer token or the local demo user header before route handlers perform application work.
- **Route Policy**: The backend module that owns route response shape and HTTP error mapping while route handlers keep URL-to-Store intent readable.
- **Runtime Composition**: The backend startup module that assembles the Store adapter, Auth Session, and Route Policy so deployment-specific wiring can change without rewriting route handlers.
- **Runtime Store Backend**: The configured Store adapter mode. `local` uses the Store Snapshot for local demos; `postgres` uses Postgres runtime connections through the Postgres adapter.
- **Production Config Guardrail**: The Runtime Composition validation step that keeps local defaults usable for demos while refusing insecure production settings such as the local Store adapter or the development JWT secret.
- **Production Runtime Entrypoint**: The package and script contract for starting RankKit services without development reload behavior.
- **Backend Container Image**: The Docker build artifact for the FastAPI API, containing runtime dependencies, API code, Alembic migrations, and a healthchecked uvicorn command.
- **CI Verification**: The GitHub Actions workflow that checks tests, production web build, browser smoke, migrations, and Postgres adapter smoke before deploy work is trusted.
- **CDK Network Foundation**: The AWS infrastructure module that defines the deployable VPC, public/private subnet layout, NAT, and security-group seams for ALB, ECS, RDS, and cache resources.
- **RankKit Client**: The web module that converts backend transport responses into RankKit domain values for screens and workflows.
- **Postgres Schema**: The future database table shape for RankKit users, leagues, members, invites, matches, and rating history; separate from the local Store Snapshot until a real adapter is implemented.
- **Postgres Match Persistence**: The Postgres adapter module that owns Match row writes, Match row hydration, rating-result serialization, and Rating History write ordering behind the Store adapter seam.

## Architectural Vocabulary

Architecture reviews should use: module, interface, implementation, depth, seam, adapter, leverage, and locality.
