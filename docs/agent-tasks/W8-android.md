# Task W8-android — Capacitor app, APK built in CI, alpha prerelease on GitHub

Branch: `feat/android`. Work in a new `apps/mobile/`, `.github/workflows/`, `docs/`. Model tier: sol.

The web app is deployed at **https://tsuyulabo.vercel.app** (public demo mode; the API is not deployed yet). There is
no Android SDK on the owner's PC, so the APK must be built by GitHub Actions (ubuntu runners have the SDK + JDK 17).

1. `apps/mobile/` npm workspace with Capacitor (latest stable; add it to the root `workspaces`): app id
   `app.tsuyulabo.alpha`, name 「ツユラボ α」. Load the deployed site via `server.url` (configurable with env
   `TSUYU_APP_URL`, default the Vercel URL) plus a small bundled `www/` offline page in the same visual style (egg art
   is fine as an inline SVG copied from `apps/web/src/components/art/Stages.tsx`) shown when offline. Generate the
   `android/` project (`npx cap add android`) and commit it (without build outputs/local.properties). App icon from
   `apps/web/src/app/icon.svg` (rasterise in CI or commit generated PNGs — keep it small).
2. `.github/workflows/android.yml`: on `workflow_dispatch` and on tags `v*-alpha*`: setup Node 22 + JDK 17, `npm ci`,
   `npx cap sync android`, `./gradlew assembleDebug`, upload the APK as an artifact, and on tags create/update a
   **GitHub prerelease** (`gh release create "$TAG" --prerelease --title ... --notes-file ...`) with the APK attached
   as `tsuyulabo-<tag>-debug.apk`. Release notes (Japanese) generated from `docs/releases/<tag>.md` — write
   `docs/releases/v0.1.0-alpha.1.md`: what the alpha contains, that it is a debug-signed build, how to install
   (allow unknown sources), that the backend is not public yet (demo mode), and known limitations.
3. Release signing is out of scope (owner will create a keystore later): document the steps in `docs/mobile.md`
   (keystore creation, GitHub secrets, `assembleRelease`/`bundleRelease`), plus the iOS path (requires macOS + Xcode +
   Apple Developer account; `npx cap add ios` on a Mac; TestFlight) — no iOS build now.
4. Validate what you can locally: `npx cap doctor`, workflow YAML with actionlint if available. Do not create tags or
   releases yourself.

Done when: configs committed, docs written, web build still passes. Atomic commit plan entries.
