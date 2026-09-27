# 迷路レース（Phase 2）

## Weekly competition

The ISO week in Asia/Tokyo (Monday 00:00 through the following Monday 00:00)
selects one shared 9×9 maze. Use the real server clock, never a player's debug
clock offset. A SHA-256 seeded depth-first carving algorithm joins odd-coordinate
rooms; start is (1,1), goal is (7,7). Coordinates are zero-based; walls are `#`.
The returned deadline is exclusive. Submissions include the displayed week so a
stale editor cannot accidentally enter next week's race.

Each player has one current entry per week. Re-entry replaces that entry with a
new ID and job; previous jobs/replays remain historical but never enter ranking.
Only owned adults may enter. Freeze the adult brain state at submission. Currency,
level, equipment and paid cosmetics never enter the simulation. There is no fee
or material consumption and no race reward affecting future results.

## Strategy and simulation v1

Place zero to three tokens on distinct open cells, including start/goal. Each cue
is from the training list: banana, apple_vinegar, yeast, grape, blue_light. Repeated
cues are allowed. Blue light uses its learned visual cue preference as well as the
light field. All tokens have intensity 1.

At each step sample forward/left/right/stay from `tsuyu_brain.api.maze_policy`.
Forward advances one open cell; left/right rotate 90 degrees in place. Headings
0/1/2/3 mean north/east/south/west; initial heading is east. A blocked forward has
zero probability; rotating remains possible at dead ends. The run stops at the
goal or after 400 actions. Replay includes the initial frame and every action.

For current and adjacent open cells, cue intensity is the sum of
`exp(-shortest_open_path_distance / 3)` from matching tokens. Walls block scent;
there is no Euclidean shortcut. Directional light is a weaker goal beacon with
the same decay, plus blue-light tokens. The policy uses directional differences
from the current cell, cached `preference_index` from the adult's olfaction_mb
state, and a cached steering circuit response. The lightweight rate readout
combines these with turn_asymmetry, light_gain, orn_gain and walking_gain. This is
a model of behavior, not a claim of a complete biological fly simulation. Fixed
neural probe seeds and SHA-256(week + user ID) action seed make a frozen input
reproducible. Cache probes once per state/cue; 400 policy steps target <1 second.

Finishers rank first by steps to goal. Others rank by shortest path distance left
after 400 steps. Equal scores share a rank; user ID supplies stable display order.
Ranking includes only the current player and their current friends, completed
entries only. Replay access follows the same ownership/friendship rule (404 for
others). Failed and pending entries remain visible to their owner for retry.

## Persistence and HTTP

Migration 0008 (down_revision 0007) adds `maze_races` (week PK, maze, deadline),
`maze_entries` (ID, week, owner, adult, placements, job, submitted_at), and
`maze_slots` (owner/week composite PK, current entry ID). Job params contain the
immutable maze, placements, brain snapshot and seed; job result contains reached,
steps, distance_left and frames. Only the slot pointer selects the current entry.

- `GET /v1/races/current`: week, maze, deadline, my_entry (including job status).
- `POST /v1/races/current/entry`: `{week, adult_id, placements:[{x,y,cue}]}`;
  requires Idempotency-Key, returns entry and enqueues `brain.maze_run` after commit.
  Inline mode executes the same simulation directly through the inline job queue.
- `GET /v1/races/current/ranking`: week and ranked completed current entries.
- `GET /v1/races/entries/{id}/replay`: frozen maze, placements, status and result.

The existing jobs endpoint can poll pending work. Replacement is serialized by
the owning user lock; the unique slot key enforces one current entry per week.

## Web

`/race` shows the deadline, selectable adults with learned preference bars, cue
chips and a tap-to-toggle token editor (maximum three). Show Japanese feedback
for invalid/full placement and submission errors. Empty collections link to home.
Poll pending jobs, offer retry for failures, and refresh friend ranking after a
run. Replay shows Tsuyu art with heading, step counter, play/pause, restart and
speed control. Respect reduced motion by starting paused. Include モデル TruthBadge
and entry cards on home and friends pages. No paid feature affects race outcomes.
