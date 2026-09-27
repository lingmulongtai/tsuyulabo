# Web API layer

Run `npm.cmd run gen:api -w apps/web` at the repository root (or `npm.cmd run gen:api`
inside `apps/web`). Generation reads the checked-in `openapi.json`; it never needs a
running API. Commit `schema.d.ts` with contract changes.

The exported API currently describes many responses as `dict[str, Any]`.
`scripts/response-schemas.mjs` refines those responses using the API serializers and
`docs/specs/api.md`, including nullable home fields and material-count bags. Keep
these refinements synchronized until the API exports response models. The original
OpenAPI export is not rewritten. Puzzle params are checked at the engine boundary.

Set `NEXT_PUBLIC_API_URL` before building (default `http://localhost:8000`). The API
must allow the web origin with CORS. `NEXT_PUBLIC_DEV_TOOLS=1` enables the floating
clock; the API separately requires `TSUYU_DEV_TOOLS=1`.

`Providers` owns a query cache per mounted app. Import endpoint hooks from
`@/lib/api/hooks`. Queries run in the browser; a first request bootstraps one guest
and stores its bearer token in guarded localStorage. If storage is unavailable,
the token lasts for the current page session. An expired token is reported, never
silently replaced with a new guest (which would hide the player's existing data).

Mutations create a UUID for each logical action. Transport retries preserve the
request body and key. Retrying the same variables on the same mounted mutation
hook after a network/server failure reuses the key. Successful actions and
definitive rule rejections release it. Hooks invalidate home and affected queries.
Do not add a second mutation retry loop that creates new keys.

Job polling ends at `succeeded`/`failed` or an HTTP error; an HTTP error has an
explicit retry control. The meal practice route is `/care/meal?practice=1` and is
also offered automatically if issue fails because the API is unreachable. Practice
never submits rewards. Real games show the server's score, effects and random roll.

Checks: `npm.cmd run lint`, `npm.cmd run typecheck`, `npm.cmd run test`,
`npm.cmd run build` from the repository root. No API is needed for these checks.
