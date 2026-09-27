# Task W8-sumo — なわばりずもう: male-vs-male pushing bouts decided by the brain model (Phase 3)

Branch: `feat/sumo`. Work in `docs/specs/`, `services/brain/`, `services/api/`, `apps/web/`. Model tier: sol.
**Database**: ONE Alembic migration with revision id `0012` and down_revision `0010` (another branch adds `0011` in
parallel; the commander re-chains it at merge).

企画書 §6: 「オスどうしの押し合い。本物のオスも、なわばりをめぐって小競り合いをする。」 Real *Drosophila* males fight over
food/territory (lunging, wing threat, boxing); the game version is a friendly pushing bout. Results must never depend
on purchases.

1. Spec (own `docs(spec)` commit): asynchronous bouts between the player's male adult and a friend's male (or a
   weekly house opponent): a small arena around a food patch; each tick both flies choose actions (approach, lunge,
   wing threat, hold, retreat) from their brain state via a façade policy; pushes move them; leaving the ring or
   retreating 3 times loses; max ticks → decided on ring position. Deterministic given both flies' states and a seed.
   Traits matter (`brave` → retreats less, `wanderer` → moves more), level adds a small stamina bonus (cap it so
   training/traits matter more than grinding). Daily bout limit; win streak shown; small shizuku reward.
   Include one paragraph of the real biology (male aggression, octopamine) with a 本物 badge note.
2. Brain façade `sumo_policy(state, observation)` using existing circuits (escape/DNp01 for retreat tendency,
   steering for approach, feeding motivation near food) — cheap, unit-tested (brave flies retreat less, etc.).
3. API: challenge list (friends' males + house opponent), start bout (inline compute, store replay), history.
   Tests incl. determinism and ownership.
4. Web `/sumo`: pick your male and an opponent, then an animated bout replay (two fly arts facing each other on a
   round mat, push arrows, a lunge/wing-threat flourish, winner banner), plus history. Entry card on friends/home.
   Match the design system.

Re-export OpenAPI + regenerate web types. Done when: `uv run pytest`, web lint/typecheck/test/build pass. Atomic
commit plan entries.
