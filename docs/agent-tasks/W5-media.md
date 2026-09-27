# Task W5-media — screenshots and a play video for the README (portfolio)

Branch: `feat/media`. Work in `apps/web/e2e/` (a new capture spec + helpers), `docs/media/`, and `README.md`.

The plan's phase-1 goal includes 「公開URL、プレイ動画、AIの評価結果の表」. The stack is running locally
(web on `http://localhost:3000` with `NEXT_PUBLIC_DEV_TOOLS=1`, API on `http://localhost:8000`); the Playwright
golden path (`apps/web/e2e/`) already plays a whole week.

1. Add `apps/web/e2e/capture.spec.ts` (tagged / in its own Playwright project so it never runs in normal CI) that
   plays a nicer-looking week than the golden path — do the care properly so the rank is **gold or rainbow** (use
   the helpers/solvers from the golden path; make good meal placements, 3-star training, perfect cleaning /
   temperature timing computed from the params, the right pupation site) — and captures, at a 390×844 mobile
   viewport with device scale factor 2, in the **light** colour scheme and again in **dark**:
   home (larva, day 3), meal game mid-play (a line clear), training board mid-path and the ★★★ result, cleaning,
   temperature gauge, presentation (rank revealed), eclosion reveal, adult detail (behaviour animation), brain
   viewer (sugar scenario mid-playback), team with a bag to open, zukan, Shiori answer.
2. Save optimised images to `docs/media/screens/<name>-<light|dark>.webp` (keep each < 150 KB; total < 3 MB).
   Record the run as a video (Playwright `video: "on"` for that project); convert/trim it to a short
   `docs/media/playthrough.webm` (< 8 MB, ~60–90 s, speed up long waits) — if you cannot convert without new
   dependencies, keep only the raw video outside git (under `eval-results/`) and say so.
3. `README.md`: add a 「スクリーンショット」 section near the top with a tidy gallery (light screenshots in a table
   with short Japanese captions; link to the dark set) and a link to the play video. Keep the rest of the README.
4. `docs/infra.md`: how to regenerate the media (`npm.cmd run capture -w @tsuyulabo/web`).

## Done when

Images committed (plan entries), README updated, capture script documented. Normal `npm test` / lint / typecheck
still pass and the capture project is excluded from the default Playwright run. Atomic commit plan entries.
