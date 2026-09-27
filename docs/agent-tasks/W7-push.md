# Task W7-push — Web Push notifications (「ごはんの時間です」) and offline-friendly PWA

Branch: `feat/push`. Work in `services/api/`, `services/worker/`, `apps/web/`, `docs/infra.md`.
**Database**: if you need a table, use ONE Alembic migration with revision id `0010` and down_revision `0009`
(another branch adds `0009` in parallel; the commander will reconcile if your clone lacks it — to keep your tests
green, you may temporarily set down_revision `0008` and say so in your report).

企画書 §14: 「通知 Firebase Cloud Messaging（『ごはんの時間です』）」; phase 2 「アプリ化とプッシュ通知」. Start with standard
Web Push (VAPID) for the PWA so it works without Firebase; keep a provider interface so FCM can be added for the
Capacitor app later.

1. API: VAPID key settings (`VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT`; a dev helper script that
   generates a key pair into `.env` locally — never commit keys); `GET /v1/push/public-key`, `POST /v1/push/subscribe`,
   `DELETE /v1/push/subscribe`; per-user notification preferences (meal slots, eclosion night, friend activity, quiet
   hours default 23:00–07:00 JST). Use the `pywebpush` library only if it is already resolvable; otherwise implement
   the minimal VAPID JWT + aes128gcm payload encryption with `cryptography` (add it as a dependency of the API package)
   and test it against RFC 8291 test vectors.
2. Worker: a cron that, at the start of each slot (04:00 / 12:00 / 18:00 JST), sends 「ごはんの時間です」 to users with
   an active week who have not cooked in that slot yet (respecting preferences and quiet hours), plus 「羽化の夜です」
   on day 7 night. Dead subscriptions (404/410) are removed. Tests with a fake sender.
3. Web: a service worker (Next.js 16 — read `node_modules/next/dist/docs/` for the recommended PWA/service worker
   setup) that shows notifications and opens the right screen on click; a settings card (new `/settings` page linked
   from home header) to enable notifications (permission prompt only on user action) and toggle categories; a basic
   offline page for the app shell. Match the design system.
4. Docs: how to generate VAPID keys and test locally.

Done when: `uv run pytest`, web lint/typecheck/test/build pass. Atomic commit plan entries.
