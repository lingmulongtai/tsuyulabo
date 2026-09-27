# Task W8-contest — 見た目コンテスト: decorate your lab, weekly theme, friends vote (Phase 3)

Branch: `feat/contest`. Work in `docs/specs/`, `services/api/`, `apps/web/`. Model tier: sol.
**Database**: ONE Alembic migration, revision id `0011`, down_revision `0010`.

企画書 §6: 「お題に合わせて、飾った飼育室と自慢の1匹を出す。フレンドの投票で決まる。」 and §13: decorations are cosmetic;
results must never depend on purchases (no paid items exist yet — keep a `source` field so paid items can never enter
contests in the future, and test that rule).

1. Spec (own `docs(spec)` commit): decoration items (vial designs, backgrounds, bedding ornaments, hats/ribbons for
   the fly) earned for free (weekly presentation rank rewards and research rank milestones — define a small table);
   a weekly theme from the ISO week (e.g. 「梅雨の研究所」「バナナ祭り」); one entry per player (a lab layout + a
   favourite adult); voting window after entries close; each player gets 3 votes for friends' entries (not their own);
   results = votes, ties by earlier entry; small shizuku rewards for participation and top 3.
2. API: inventory of decorations, equip/layout endpoints, contest current/entry/vote/results; ownership/friend checks;
   idempotency; tests.
3. Web: a decoration editor on the lab/home terrarium (place ornaments on a few fixed slots, pick vial/background),
   render equipped items in `Terrarium` and on the adult art (hat/ribbon overlays as small SVG components in
   `src/components/art/decor/`), a `/contest` screen (theme, my entry, friends' entries to vote on with their
   terrarium previews, results with podium). Match the design system; draw the decorations as simple, clean SVGs in the
   same style as the existing art (light from the top-left, coloured outlines).

Re-export OpenAPI + regenerate web types. Done when: `uv run pytest`, web lint/typecheck/test/build pass. Atomic
commit plan entries.
