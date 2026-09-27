# 引き継ぎメモ（HANDOFF）

作業が途中で止まっても、ここを読めば続きができるようにする。**新しい作業者はまずここを読む。止まる前にここを更新する。**

## いまの状態（サマリー）

- 日付: 2026-09-27（午後）
- フェーズ: W3 完了 → W4 進行中。**アルファの1週間ループが Web + API + ワーカー + DB で通しで遊べる状態**
- main にあるもの: 全画面が API につながった Web（ホーム、ごはん・しつけ・そうじ・温度・場所えらび・睡眠、研究発表会、羽化、
  チーム、成虫の詳細＋脳モデルで動く行動、脳ビューア、図鑑、フレンド、シオリ、開発用の時計）、ゲーム API、本物の脳エンジン
  （既定は toy-v0。MaleCNS v1.0 の回路も同梱、6 項目中 3 項目合格）、シオリ、ワーカー、docker compose、CI
- テスト: Python 597 件（+ eval）、Web 254 件。ruff / typecheck / lint / build も通過。GitHub Actions も緑
- ブラウザで通しプレイ確認済み: 卵 → 時間スキップ → 発表会（ケアミスで減点・報酬 0）→ 羽化（サーバーの抽選）→ 成虫ページ → 脳ビューア
- 実行中のタスクはなし（2026-09-27 15:06 時点）。マイグレーションの先頭は 0010
- MaleCNS v1.0 の生データ（約 1.1 GB、オーナー許可済み）は `C:\Users\lingm\dev\tsuyulabo-agents\W3-malecns\data\raw\malecns-v1.0\`
  （W4-malecns-calibrate のクローンにもコピー）。git には入れない
- Codex の使用量は 11:26 頃に一度上限に達したが、オーナーが同日リセットした（再開済み）。
- **オーナー向けチェックリスト**:
  1. Vercel CLI にログインして `docs/deploy.md` の手順で Web を公開（API なしでもデモ案内のトップになる）
  2. API を公開するなら Cloud Run + Neon + Upstash（`docs/deploy.md`）。GitHub の Secrets を入れると `deploy.yml` が動く
  3. Codex のサンドボックス設定（Codex に直接コミットさせたい場合）
  4. プレイ動画を作るなら `winget install ffmpeg` → `docs/media/README.md` の 1 行を実行
  5. git の author メール（学校のアドレス）を公開リポジトリで使い続けるか決める
- オーナーが帰宅後にやること（元のメモ）: Codex のサンドボックス設定、Vercel CLI のログイン
- ローカルで pytest が `PermissionError: ...\Temp\pytest-of-lingm` になるときは `PYTEST_DEBUG_TEMPROOT=/c/Users/lingm/.cache/pytest-tmp` を付ける
  （Codex のサンドボックスが作った一時フォルダの権限のせい）。

## オーナーの希望（2026-09-27 の指示）

- 企画書 v0.2 に沿って、アルファ版（フェーズ1）まで一気に作る。
- **アトミックコミットを徹底**（数が多くなってよい）。
- Claude は指揮官。Codex（使用量に余裕あり）をどんどん使う。デザインは Claude。
- GitHub は **Public**。構成は**企画書どおりのフルスタック**。Vercel へのデプロイは OK。
- 作業フォルダは OneDrive 内のまま（問題が出たら OneDrive の外に clone し直す）。

## Codex の動かし方

- CLI: Codex デスクトップアプリ同梱の `codex.exe`（`(Get-AppxPackage OpenAI.Codex).InstallLocation\app\resources\codex.exe`）。
  `~/.codex/.sandbox-bin/codex.exe` は古くて今のモデルを使えない。
- 1タスク = 1クローン = 1ブランチ。クローンは OneDrive の外: `C:\Users\lingm\dev\tsuyulabo-agents\<task>`
- Codex は **workspace-write サンドボックス**で動かす。サンドボックス無効化（`--dangerously-bypass-approvals-and-sandbox`）は
  Claude Code の自動モードで拒否された。サンドボックスは `.git` に書けないので、Codex はコミットせず
  `.codex-runs/commits.jsonl` にコミット計画を書く → Claude が `apply-commit-plan.py` でアトミックコミットにする（AGENTS.md 参照）。
- サンドボックスはホームフォルダを読めないので、uv は各クローンの `.tools/uv.exe`、キャッシュと Python は `.uv/` に置く（スクリプトが自動でやる）。
- 手順（Git Bash、本体リポジトリで）:

```bash
scripts/agents/run-codex.sh W1-brain feat/brain-engine high      # 実行（数十分）
python scripts/agents/apply-commit-plan.py /c/Users/lingm/dev/tsuyulabo-agents/W1-brain
git fetch /c/Users/lingm/dev/tsuyulabo-agents/W1-brain feat/brain-engine
git merge --no-ff FETCH_HEAD -m "merge: brain engine (W1-brain)"
git push
```

- プロンプトは `docs/agent-tasks/<task>.md` に保存してからコミットする（何を頼んだかを残す）。
- uv はこのマシンだと既定の AppData の場所で壊れる。`UV_CACHE_DIR=~/.cache/uv`、`UV_PYTHON_INSTALL_DIR=~/.local/uv-python`、
  `UV_PYTHON_PREFERENCE=only-managed` を設定して `~/bin/uv.exe` を使う。

## タスク一覧

| id | 内容 | 担当 | ブランチ | 状態 |
| --- | --- | --- | --- | --- |
| W0-scaffold | uv / npm workspaces、Next.js と FastAPI の雛形 | Claude | main | 完了 |
| W1-brain | 脳エンジン（specs/brain.md） | Codex | feat/brain-engine | マージ済み |
| W1-domain | ゲームルールとパズルの Python 実装（specs/game-rules.md, puzzles.md） | Codex | feat/game-domain | マージ済み |
| W1-api-core | API の土台（DB、認証、時計、冪等性、台帳） | Codex | feat/api-core | マージ済み |
| W1-web-puzzles | パズルの TS エンジン、音、振動 | Codex | feat/web-puzzles | マージ済み |
| W1-design | デザインシステム、キャラクター、ホーム画面 | Claude | feat/web-design | マージ済み |
| W2-infra | docker compose、Dockerfile、CI | Codex | feat/infra | マージ済み |
| W2-api-game | ゲームのエンドポイント（domain + DB + 脳） | Codex | feat/api-game | マージ済み |
| W2-shiori-worker | シオリのエージェントと arq ワーカー | Codex | feat/shiori-worker | マージ済み |
| W2-puzzle-parity | TS のパズル検証を Python と完全一致させる | Codex | fix/puzzle-parity | マージ済み |
| W2-web-games | ごはん・しつけの画面、羽化の演出、研究発表会 | Claude | feat/web-games, feat/web-screens | マージ済み |
| W3-integration | 本物の脳を API とワーカーに接続、報酬の下限、研究ランク | Codex | feat/integration | マージ済み（docker compose で通し確認済み） |
| W4-brain-viewer | 神経活動の API と脳ビューア画面 | Codex | feat/brain-viewer | マージ済み |
| W4-wire-screens | しつけ・発表会・羽化の画面を API に接続、ホームの発表会導線 | Codex | feat/wire-screens | マージ済み |
| W4-malecns-calibrate | 本物の回路の調整（3/6 → 5/6 合格。デコーダーだけ未達、既定は toy-v0） | Codex | feat/malecns-calibrate | マージ済み |
| W4-names | 成虫の名前の自動生成と名前の変更 | Codex | feat/adult-names | マージ済み |
| W4-e2e | Playwright で1週間を通しでプレイ（ローカルで 2.8 分で合格） | Codex | feat/e2e | マージ済み |
| W5-media | README 用のスクリーンショット 30 枚（15 場面 × ライト/ダーク）。動画はフル FFmpeg が必要なので未作成 | Codex → Claude | feat/media | マージ済み |
| W7-omiai | お見合い（フレンドの成虫と交配、両方に卵） | Codex | feat/omiai | マージ済み |
| W7-push | Web Push 通知（ごはんの時間です）、通知設定、オフライン用の PWA 画面（実機での配信は未確認） | Codex | feat/push | マージ済み |
| W5-deploy | Vercel と Cloud Run のデプロイ設定、手順書 `docs/deploy.md`（実デプロイはオーナー） | Codex | feat/deploy | マージ済み |
| W5-daily-circuit | 今日の回路（全員同じ問題、フレンドのタイムランキング） | Codex | feat/daily-circuit | マージ済み |
| W5-breeding | 交配と本物の遺伝（伴性遺伝、Cy のホモ致死）、系統図鑑 | Codex | feat/breeding | マージ済み |
| W5-decoder | MaleCNS のデコーダーを 85% 以上に（78% で未達。出力ニューロンが沈黙する回路の限界。既定は toy-v0） | Codex | feat/malecns-decoder | マージ済み |
| W6-maze-race | 迷路レース（置いた匂いと、しつけ・特性で脳モデルが走る。リプレイ、フレンドランキング） | Codex | feat/maze-race | マージ済み |
| W6-circadian | いっしょにねる（体内時計ゲージ、げんき回復の倍率） | Codex | feat/circadian | マージ済み |
| W6-review | API のセキュリティ・正確性レビューと 8 件の修正（`docs/security-review.md`） | Codex | fix/api-review | マージ済み |
| W6-shiori-answers | シオリの Mock 回答を話題別に、引用は関連する少数だけに | Codex | feat/shiori-answers | マージ済み |
| W3-web-app | API クライアント、フック、ホームとごはんの接続、残りの画面 | Codex | feat/web-app | マージ済み |
| W3-malecns | MaleCNS v1.0 から回路を作って評価（3/6 合格、既定は toy-v0 のまま） | Codex | feat/malecns | マージ済み |

## 決めたこと（理由つき）

- 研究週は「卵を受け取った日 = 1日目」（暦の月曜にそろえない）。途中から始めた人が待たなくていいように。
- 1日の区切りは 04:00 JST。企画書の時間帯（朝 4:00〜）に合わせた。
- パズルは「サーバーが問題の中身を渡し、操作の記録を送り返して、サーバーが再生採点」。乱数の実装を TS と Python でそろえる必要をなくすため。
- 配線データは、アルファでは実名に合わせた合成配線 `toy-v0`。本物（MaleCNS）の取り込みスクリプトは用意するが、データのダウンロードはオーナーの確認後。
- シオリは API キーなしで全部動く MockProvider を既定にする。キーを入れれば Anthropic / OpenAI に切り替わる。

## 未解決・オーナーに確認したいこと

- git の author が学校のメールアドレス（`2025m011@kuas.ac.jp`）。Public リポジトリなのでコミットに表示される。気になるなら GitHub の noreply アドレスに変える。
- Vercel CLI は未インストール・未ログイン。デプロイにはオーナーのログインが必要かもしれない。
- 本物の配線データ（MaleCNS）のダウンロード可否。

## Log

- 2026-09-27 昼 Claude: 使用量の上限で停止。再開手順:
  1. 実行中だった Codex（W2-api-game, W2-shiori-worker）の結果を C:\Users\lingm\dev\tsuyulabo-agents\<task>.last.md で確認。
  2. 終わったタスクごとに python scripts/agents/apply-commit-plan.py <clone> → main で git fetch <clone> <branch> → git merge --no-ff → テスト → push。
     対象: W2-infra (feat/infra), W2-puzzle-parity (fix/puzzle-parity), W2-api-game (feat/api-game), W2-shiori-worker (feat/shiori-worker)。
  3. feat/web-games を main にマージ（/care/meal でごはんづくりの練習ができる）。
  4. 次: しつけ・そうじ・温度・場所えらびの画面、羽化と発表会の画面、API クライアントで画面をつなぐ、Vercel デプロイ。

- 2026-09-27 Claude: リポジトリ作成。企画書、開発計画、仕様（game-rules / puzzles / api / brain / shiori）、AGENTS.md を追加。
- 2026-09-27 昼 Claude: スクリーンショット撮影で「羽化後にシオリへの質問が失敗する」バグを発見・修正（最新の週にフォールバック）。
  発表会のランクのしきい値が低すぎた（上手に遊ぶと 8.2 万点、にじは 1.6 万点から）ので 2.5 万 / 4.5 万 / 7 万に変更。
  並列ブランチで同じ Alembic リビジョン 0006 ができたので、genetics を 0007 に振り直した。
- 2026-09-27 15:06 Claude: W7（お見合い、Web Push）をマージ。push のマイグレーションを 0009 の後ろに付け替え。docker compose を 0010 まで上げて
  `scripts/smoke_api.py` が通ることを確認。次の候補: 見た目コンテスト、なわばりずもう（フェーズ3）、Capacitor でアプリ化、
  シオリの実 LLM（API キーが必要）、MaleCNS デコーダーの改善（出力ニューロンの追加抽出）、プレイ動画（フル FFmpeg が必要）。
- 2026-09-27 夕方 Claude:
  - **学校のメールアドレスを履歴から削除**（オーナーの指示）。全 474 コミットの author/committer を
    `218745625+lingmulongtai@users.noreply.github.com` に書き換えて main を強制 push。古い feat ブランチは削除。
    このリポジトリと Codex クローンの `user.email` は noreply に設定済み。`run-codex.sh` と `apply-commit-plan.py` は
    noreply 以外だと止まる。CI の `commit-identity` ジョブも noreply 以外のメールがあれば失敗する。**今後も絶対に学校のアドレスを使わない。**
  - **Vercel に公開**: https://tsuyulabo.vercel.app （プロジェクト `tsuyulabo`、Root Directory `apps/web`、`NEXT_PUBLIC_DEV_TOOLS=0`、
    API URL なし＝公開デモモード）。再デプロイはルートで `vercel deploy --prod --yes`。Git Bash で `vercel api` を使うときは `MSYS_NO_PATHCONV=1`。
  - **Codex の使用量を抑える**: `run-codex.sh <task> <branch> [effort] [model]`。既定は gpt-6-sol / medium。
    難しい研究だけ gpt-6-astra、簡単な作業は gpt-6-luna。
  - W8 を投入: Capacitor Android + CI で APK + GitHub プレリリース（sol）、見た目コンテスト（sol、migration 0011）、
    なわばりずもう（sol、migration 0012 → マージ時に 0011 の後ろへ）、MaleCNS デコーダー改善（astra）。
- 2026-09-27 夕方 Claude: W8-android / W8-sumo / W8-contest をマージ（マイグレーションは 0010 → 0011 コンテスト → 0012 ずもう）。
  Android の CI は 4 回目で成功（setup-android をやめてランナーの SDK を使う、Gradle の versionName の括弧、JDK 21）。
  **プレリリース v0.1.0-alpha.1 を公開**: https://github.com/lingmulongtai/tsuyulabo/releases/tag/v0.1.0-alpha.1
  （デバッグ署名 APK 4.3 MB。アプリは Vercel の公開デモを読み込む）。次のアルファは docs/releases/<tag>.md を書いてから `v0.1.0-alpha.N` タグを push。
