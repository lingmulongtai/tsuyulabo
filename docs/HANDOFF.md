# 引き継ぎメモ（HANDOFF）

作業が途中で止まっても、ここを読めば続きができるようにする。**新しい作業者はまずここを読む。止まる前にここを更新する。**

## いまの状態（サマリー）

- 日付: 2026-10-01。開発は新しい PC（ROG Zephyrus G14）に移った。**作業場所は `C:\Users\lingm\dev\tsuyulabo`**
  （OneDrive の外）。OneDrive 内の古いコピーは使わない（OneDrive の同期で git が固まった）。セットアップは [NEW_PC.md](NEW_PC.md)。
- **本番が遊べる**: https://tsuyulabo.vercel.app で育成・フレンドまで遊べる。API は**オーナーの PC で自宅サーバー**として動く
  （[selfhost.md](selfhost.md)）: Docker のプロジェクト `tsuyulabo-server`（本番用 clone `C:\Users\lingm\srv\tsuyulabo`）→
  Tailscale Funnel `https://ozg14.tail4204cd.ts.net` → Vercel が `/v1` を転送。秘密の値は `~/.tsuyulabo/selfhost.env`。
  デプロイは `scripts/selfhost/deploy.ps1`（push 済みの `origin/main` を出す）。
- フェーズ: アルファ（フェーズ1）完成 → フェーズ2・3 の機能も main に入った。
- **実行中**: シオリ専用モデルの LoRA 学習 v1（Claude が WSL2 Ubuntu で実行。`~/shiori-gpu/adapter-v1`、1 エポック 250 ステップ、
  1 ステップ約 45 秒。ログは `~/.tsuyulabo/train-v1.log`）。手順は `ml/shiori-lora/README.md`。WSL には build-essential と
  flash-linear-attention を追加済み（入れないと 2.2 倍遅い）。
- サーバーの守り（W12）: 本番は `RATE_GUEST_HOUR=60`（Funnel が XFF を Vercel の IP で上書きするので、IP ごとの上限は
  ゆるくし、全体の 1 日 200 人で守る）。値は `~/.tsuyulabo/selfhost.env`。
- シオリのローカル LLM（W9/W10、[local-llm.md](../services/shiori/reports/local-llm.md)）: 既製の qwen3.5:4b は回数の正答率
  33〜64%、根拠を落とす。2b はほぼ 0%。本番の既定は Mock のまま。次は LoRA で自前のモデルを作る。
- main にあるもの:
  - **1週間の育成ループ**: ホーム、ごはん（ブロックパズル）、しつけ（回路パズル）、そうじ、温度、場所えらび、睡眠、研究発表会、
    羽化（サーバーの抽選）。すべて API につながっている。
  - **羽化のあと**: 研究チーム、成虫の詳細（脳モデルで動く行動）、名前、脳ビューア、図鑑、フレンド、シオリ、交配と本物の遺伝、
    お見合い、迷路レース、今日の回路、いっしょにねる、Web Push、**見た目コンテスト**、**なわばりずもう**。
  - **脳エンジン**: 既定は本物の配線 **MaleCNS v1.0**（6 項目すべて合格、デコーダー 88.6%）。合成の `toy-v0` も同梱。
  - シオリ（Mock で全部動く。API キーを入れると Anthropic / OpenAI）、arq ワーカー、docker compose、CI 5 本
    （ci / eval / e2e / deploy / android）、Capacitor の Android アプリ。
- テスト: Python 621 件 + eval 7 件、Web の lint / typecheck / test / build、Playwright の1週間通しプレイ。
  CI の `api-postgres`（失敗しても止めないジョブ）だけ以前から赤い（テスト 2 件が CI の環境変数を拾う）。
- マイグレーションの先頭は **0012**（0011 コンテスト → 0012 ずもう）。
- 実装の担当: **Codex**（`run-codex.sh`、既定 gpt-6.1-sol。上限が 10% 以下ならリセットを使ってよい）と **Antigravity**
  （アプリと IDE にサインイン済み。CLI の `antigravity-ide chat` は指示がエージェントに届かず、自動化は保留。
  Codex が上限のときは、指示書をオーナーが Antigravity に貼る。下書きは `~/.tsuyulabo/drafts/`）。
- バックアップ: 毎朝 5:00 にタスク スケジューラ「tsuyulabo-backup」が C ドライブと F ドライブ（USB の外付け SSD）に取る。
- この PC の注意: **CPU が冷えない**（液体金属の劣化）。長い CPU の処理は避ける（全テストは約 9 分）。GPU は冷える。
  電源モードが省電力だと GPU が 390 MHz に張り付いてローカル LLM が 10 倍以上遅くなる（バランスなら qwen3.5:4b で 42 トークン/秒）。
- **オーナー向けチェックリスト**（残り）:
  1. スタートアップの「DJIStudio.quicklook」をオフにする（裏で GPU を使う）。
  2. Android の本番署名用の keystore を作る（`docs/mobile.md`）。iOS には Mac・Xcode・Apple Developer が必要。
  3. GitHub の「Keep my email addresses private」を有効にする。
- 次の候補:
  - **LoRA で学習したシオリ専用モデル**（`tsuyu-shiori:2b-lora-v1`、`ml/shiori-lora/README.md`）を評価し、合格なら本番を
    `SHIORI_PROVIDER=ollama` に切り替える（worker から `host.docker.internal:11434`）。その次は ③ 夜の研究日誌用の小さい GPT を一から。
  - 脳: 一部の匂い（酵母）の反応が「じっとしている」にまとまる。検証用データでは 81.8%。
  - Web Push の実機での配信確認、プレイ動画。

## オーナーの希望（2026-09-27 の指示）

- 企画書 v0.2 に沿って、アルファ版（フェーズ1）まで一気に作る。
- **アトミックコミットを徹底**（数が多くなってよい）。
- Claude は指揮官。Codex（使用量に余裕あり）をどんどん使う。デザインは Claude。
- GitHub は **Public**。構成は**企画書どおりのフルスタック**。Vercel へのデプロイは OK。
- 作業フォルダは OneDrive 内のまま（問題が出たら OneDrive の外に clone し直す）。→ 2026-09-29 に問題が出たので外に移した。

## オーナーの希望（2026-09-29 / 10-01 の指示）

- この PC をサーバーにしてよい。AI（シオリの LLM）もこの PC でローカルに動かしてよい。
- 優先順位: ① API をこの PC で公開 → ② シオリをローカル LLM → ③ 自作 LLM（LoRA まで）→ ④ 磨き込み・新機能。
- 公開は Tailscale Funnel。Antigravity には Claude から自動で渡す。ローカル AI は「既製モデル → LoRA」まで。
- 実装は Codex と Antigravity の両方を使ってよい（Codex は上限が近いとき使用量リセットを使ってよい）。
- Claude も多めに使ってよいが、5 時間の上限があるので配分に気をつける。
- DJI Studio が裏で GPU を使うのは嫌なので、止めてよい。CPU は冷えないので無理をさせない。

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
| W9-selfhost | オーナーの PC で API を本番公開（Docker、Tailscale Funnel、Vercel の転送、バックアップ） | Claude | main | 完了 |
| W9-shiori-local | シオリをローカル LLM（Ollama）で動かし、実モデルで評価する（4B 64% / 2B 2%、既定は Mock） | Codex | feat/shiori-local | マージ済み |
| W10-shiori-tools | 小さいモデル向けのツール（絞り込み、回数の集計、日本語の選択肢）と open 質問の評価（4B 33%、悪化） | Codex | feat/shiori-tools | マージ済み |
| W11-shiori-lora-data | LoRA 用の理想の手本データと、WSL2 で動かす学習・書き出しスクリプト | Codex | feat/shiori-lora-data | マージ済み |
| W12-server-guard | Redis のレート制限、ゲスト作成の上限、ジョブの受付制限、worker の同時実行 2 | Codex | feat/server-guard | マージ済み |

## 決めたこと（理由つき）

- 研究週は「卵を受け取った日 = 1日目」（暦の月曜にそろえない）。途中から始めた人が待たなくていいように。
- 1日の区切りは 04:00 JST。企画書の時間帯（朝 4:00〜）に合わせた。
- パズルは「サーバーが問題の中身を渡し、操作の記録を送り返して、サーバーが再生採点」。乱数の実装を TS と Python でそろえる必要をなくすため。
- 配線データは、アルファでは実名に合わせた合成配線 `toy-v0`。本物（MaleCNS）の取り込みスクリプトは用意するが、データのダウンロードはオーナーの確認後。
- シオリは API キーなしで全部動く MockProvider を既定にする。キーを入れれば Anthropic / OpenAI に切り替わる。

## 未解決・オーナーに確認したいこと

- （2026-09-27 に全部解決: メールは noreply に変えて履歴も書き換え、Vercel は公開済み、MaleCNS はダウンロード済み）

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
- 2026-09-27 夕方 Claude: W8-decoder をマージ。MaleCNS から出力ニューロン 279 個を追加抽出し、デコーダーが 88.6%（検証用データでは 81.8%）。
  **6 項目すべて合格したので、ゲームの既定の脳を本物の配線 `malecns-v1.0` に切り替えた。** Python 618 件 + eval 7 件が通過。
  docker compose でも本物の配線で `scripts/smoke_api.py` が通ることを確認。残りの課題: 一部の匂いの反応が「じっとしている」にまとまる。
- 2026-09-29 Claude: 開発を別の PC に移すため、再開の手順を [NEW_PC.md](NEW_PC.md) にまとめ、このサマリーを最新にした。
  `run-codex.sh` のクローンと uv の場所を、ユーザーのホームフォルダから決めるようにした（旧 PC では同じ場所になる）。
- 2026-09-29 Claude（新しい PC）: ドキュメントを読んで引き継ぎ。オーナーに方針を確認（上の「2026-09-29 / 10-01 の指示」）。
  OneDrive 内で `.venv` を作り直したら OneDrive の同期で git と pytest が固まったので、作業場所を `C:\Users\lingm\dev\tsuyulabo` に移した。
  自宅サーバー用の compose（`docker-compose.selfhost.yml`）、秘密の値の生成、デプロイ・バックアップのスクリプト、`docs/selfhost.md` を追加。
  Ollama で小さいモデルを試した（gemma4:e4b は 6 GB の GPU に収まらない → qwen3.5:4b / 2b を採用）。W9-shiori-local の指示書を書いた。
- 2026-10-01 Claude: WSL2 と Docker Desktop が入ったので**本番を公開**。`deploy.ps1` で `tsuyulabo-server` を起動、Tailscale Funnel で
  `https://ozg14.tail4204cd.ts.net` に出し、Vercel を本番モードで再公開。Tailscale につないだ端末では API の名前が 100.x になり、
  Chrome の Local Network Access に止められたので、**Vercel が `/v1` を自宅サーバーへ転送する方式**にした（`TSUYU_API_PROXY_TARGET`）。
  あわせて API に Private Network Access の応答を追加。Playwright で本番のゲスト作成とホーム表示を確認。
  CPU が冷えない PC なので api / worker を 2 コアずつに制限。電源モードをバランスにしたらローカル LLM が 2.7 → 42 トークン/秒に。
  W9-shiori-local を Codex（gpt-6.1-sol）に投入。
