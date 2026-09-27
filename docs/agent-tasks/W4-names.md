# Task W4-names — give each adult a name, and let the player rename it

Branch: `feat/adult-names`. Work in `services/api/` and `apps/web/`.

A live playthrough showed every eclosed adult is called 「ショウジョウバエ」. Fix:

1. **Domain** (`services/api/src/tsuyulabo_api/domain/`): a pure `names.py` with a pool of ~60 short, cute Japanese
   names that fit the theme (dew, fruit, light, research: e.g. つゆまる, しずく, こはく, ぴかり, もなか, すだち, ルビー,
   あめ, みつ, ほたる, …) and `pick_name(rng, taken: set[str]) -> str` that avoids names the user already has
   (fall back to adding a number: しずく2). Mutant strains may prefer themed names (white → ゆき / しろ系, ebony →
   くろまめ系 …). Unit tests.
2. **Eclosion** uses it with the server RNG (deterministic given the seed); existing rows keep their names.
3. **Rename**: `PATCH /v1/adults/{id}` with `{ "name": "..." }` (1–12 characters after trimming, no control
   characters; error `validation_error`), idempotency like other mutations. Tests.
4. Re-export OpenAPI (`services/api/scripts/export_openapi.py`) and regenerate web types (`npm.cmd run gen:api`).
5. **Web**: on `/adults/[id]` (component `src/components/collection/AdultDetail.tsx`) add a small pencil button next
   to the name that opens an inline edit field (same design language: rounded input, chunky save button), using a
   new `useRenameAdult` hook in `src/lib/api/hooks-collection.ts`. The eclosion reveal already shows the name from
   the server.

## Done when

`uv run pytest services/api`, ruff, and web lint/typecheck/test/build pass. Atomic commit plan entries.
