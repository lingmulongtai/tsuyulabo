# 引き継ぎメモ（HANDOFF）

作業が途中で止まっても、ここを読めば続きができるようにする。**新しい作業者はまずここを読む。止まる前にここを更新する。**

## いまの状態（サマリー）

- 日付: 2026-09-27（午前）
- フェーズ: W1 ほぼ完了 → W2 進行中
- main にあるもの: 仕様一式、uv / npm workspaces、Next.js 16 の雛形、デザインシステム・キャラ・ホーム画面（モック）、
  パズルの TS エンジンと音、Python のゲームルール（domain）と共有 fixtures、API の土台（DB・認証・時計・冪等性・台帳）
- 次にやること: 走っている Codex タスクの結果をマージ（下の表）。Claude はミニゲーム画面（`feat/web-games`）→ 羽化・発表会の画面 →
  API クライアントで画面をつなぐ。
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
| W1-brain | 脳エンジン（specs/brain.md） | Codex | feat/brain-engine | 実行中 |
| W1-domain | ゲームルールとパズルの Python 実装（specs/game-rules.md, puzzles.md） | Codex | feat/game-domain | マージ済み |
| W1-api-core | API の土台（DB、認証、時計、冪等性、台帳） | Codex | feat/api-core | マージ済み |
| W1-web-puzzles | パズルの TS エンジン、音、振動 | Codex | feat/web-puzzles | マージ済み |
| W1-design | デザインシステム、キャラクター、ホーム画面 | Claude | feat/web-design | マージ済み |
| W2-infra | docker compose、Dockerfile、CI | Codex | feat/infra | 実行中 |
| W2-api-game | ゲームのエンドポイント（domain + DB + 脳） | Codex | feat/api-game | 実行中 |
| W2-shiori-worker | シオリのエージェントと arq ワーカー | Codex | feat/shiori-worker | 実行中 |
| W2-puzzle-parity | TS のパズル検証を Python と完全一致させる | Codex | fix/puzzle-parity | 実行中 |
| W2-web-games | ミニゲーム画面（ごはん、しつけ、そうじ、温度、場所えらび） | Claude | feat/web-games | 進行中 |

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

- 2026-09-27 Claude: リポジトリ作成。企画書、開発計画、仕様（game-rules / puzzles / api / brain / shiori）、AGENTS.md を追加。
