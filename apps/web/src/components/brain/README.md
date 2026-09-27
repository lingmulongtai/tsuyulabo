# Brain viewer integration

Open `/adults/<adult-id>/brain` for a saved adult. `/adults/<adult-id>` provides
a minimal adult summary and a link to the viewer; this branch did not previously
have an adult detail page. The endpoint also accepts the active week ID for its
larva, following the existing behavior endpoint's convention.

The shared web account/client flow is not present on this branch. `BrainConnection`
therefore reads the existing guest JWT from `localStorage["tsuyulabo.token"]`, or
offers a password field for connecting with it. It does not create a replacement
guest. Use the token returned by `POST /v1/auth/guest` for the user who owns the fly.
Reconnect removes this local token and lets the user enter another one.

`NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000`. Set it before
starting or building the web app when the API has a different address. An empty
value uses the web origin (for deployments that proxy `/v1`). The API must allow
the web origin through its existing `cors_origins` setting.

From the repo root on Windows, with the existing API/database configured:

```powershell
.\.tools\uv.exe run uvicorn tsuyulabo_api.main:app --port 8000
npm.cmd run dev -w apps/web
```

The response contains 23 groups, signed edge weight sums, and 20 equal windows
covering 300 ms. The viewer starts paused and plays one window every 250 ms for
inspection; the time labels show simulation time. Scrubbing pauses playback.
Switching scenarios cancels the old request and resets playback.

Both odor scenarios present banana, matching the existing behavior engine. Their
names do not force a preference or retrain the fly. DANs remain inactive during
observation. The diagram's real-name badge identifies biological naming only:
the wiring and rates are explicitly labeled as a synthetic model.

The API cache is a process-local LRU of 128 responses, keyed by owner, fly ID,
SHA-256 of the complete brain snapshot, and scenario. Ownership is checked on
every request, including cache hits. Changed learned weights or individual
parameters produce a different version key. Browser responses are fetched with
`cache: "no-store"`. No new frontend dependencies are required.
