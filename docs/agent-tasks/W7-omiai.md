# Task W7-omiai — お見合い: mate with a friend's adult, both players get an egg

Branch: `feat/omiai`. Work in `docs/specs/genetics.md` (+ `game-rules.md` §12), `services/api/`, `apps/web/`.
**Database**: if you need a table, use ONE Alembic migration with revision id `0009` and down_revision `0008`.

企画書 §6: 「お見合い: フレンドの成虫と交配して、両方に卵が届く。」 The endpoint exists as a 501 stub (breeding task).

1. Spec: a player proposes (their adult + a friend's adult of the other sex); the friend accepts or declines
   (proposals expire after 48 h); on accept, each player gets a hidden egg drawn independently from the same two
   parents (real genetics from `domain/genetics.py`), usable as their next week's egg (a player with a running
   week keeps it pending until they start a week); one proposal per pair per week; both adults marked as used for
   that week. Notifications to both players. Nothing purchasable affects it.
2. API: propose / list incoming+outgoing / accept / decline / start-week-from-pending-egg; ownership + friendship
   checks; idempotency; tests incl. genetics determinism and the 48 h expiry via the dev clock. Re-export OpenAPI.
3. Web: on a friend's lab page (`/friends/[id]`) a 「お見合いを申し込む」 button next to their adults (choose your
   adult of the other sex, show the offspring prediction using the existing Punnett helper), an inbox card on
   `/friends` for incoming proposals (accept/decline), and on home (no running week) show pending eggs as a choice
   next to 「卵を受け取る」/「交配する」. Match the design system.

Done when: `uv run pytest`, web lint/typecheck/test/build pass. Atomic commit plan entries.
