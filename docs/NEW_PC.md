# 別の PC で開発を再開する

2026-09-29 に、開発を別の PC へ移した。このファイルは、新しい PC で同じように開発を続けるための手順。
進み具合と決めたことは [HANDOFF.md](HANDOFF.md)、作業のルールは [AGENTS.md](../AGENTS.md) にある。

## 0. 最初に必ず：コミットのメールアドレス

**学校のメールアドレスは、コミットに絶対に使わない**（オーナーの指示。2026-09-27 に過去の全コミットから削除済み）。
clone した直後、何かをコミットする前に、リポジトリで次を実行する。

```bash
git config user.name lingmulongtai
git config user.email 218745625+lingmulongtai@users.noreply.github.com
```

- 新しい PC の `git config --global user.email` も確認する。学校のアドレスなら noreply に変えておくと安全。
- 守りは 3 か所: CI の `commit-identity` ジョブ、`scripts/agents/run-codex.sh`、`scripts/agents/apply-commit-plan.py`。
  noreply 以外のメールだと、どれも止まる。
- GitHub の設定「Keep my email addresses private」も有効にしておくとよい。

## 1. 入れるもの

| もの | 用途 | メモ |
| --- | --- | --- |
| Git for Windows（Git Bash） | スクリプトは Git Bash で動かす | |
| Node.js 20.9 以上 | Web | 旧 PC は v26.4 / npm 11.18 |
| uv | Python（3.13 は uv が入れる） | 旧 PC は 0.12.19 |
| Docker Desktop | `docker compose up` で全部入り | |
| GitHub CLI | CI の確認、リリース | `gh auth login` |
| Vercel CLI | Web の公開 | `npm i -g vercel` → `vercel login` |
| Codex デスクトップアプリ | 実装担当の Codex | アプリにログイン。CLI はアプリ同梱の `codex.exe` を使う |
| Claude Code | 指揮とデザイン | |
| （任意）JDK 21 + Android SDK | APK をローカルで作るとき | CI（`android.yml`）でも作れる |
| （任意）FFmpeg のフル版 | README のプレイ動画 | `winget install ffmpeg` |

## 2. リポジトリを取ってくる

```bash
git clone https://github.com/lingmulongtai/tsuyulabo.git
```

- 旧 PC の作業フォルダは OneDrive 内（`OneDrive - 学校法人　永守学園\.Projects\tsuyulabo`）。OneDrive で同期されたものは
  そのまま使わず、clone し直すのが安全:
  - `.venv` と `node_modules` は旧 PC の絶対パスを持っていて、別の PC では動かない。
  - 2 台で同時に `.git` を触ると壊れる。**作業する PC は 1 台だけにして、切り替える前に push、始める前に pull。**
- OneDrive に置き続けたい場合も、中身は git で同期する（`git pull`）。
- **2026-09-29 の新しい PC では `C:\Users\lingm\dev\tsuyulabo` に clone した。** OneDrive 内で `.venv`（約 2 万ファイル）を
  作り直したら、OneDrive の同期にファイルをつかまれて `git commit` も pytest も固まった。OneDrive の外に置くこと。

## 3. 動かす

```bash
docker compose up                 # web, api, worker, postgres, redis（マイグレーションの先頭は 0012）
```

Docker なしで:

```bash
uv sync --all-packages
npm install
uv run pytest                     # Python（618 件）
uv run pytest -m eval             # 脳とシオリの評価（本物の配線のシミュレーションで約 10 分）
npm test                          # Web
uv run python scripts/smoke_api.py   # 動いているスタックを通しで試す
```

詳しくは [infra.md](infra.md)。旧 PC で出た不具合と回避策:

- pytest が `PermissionError: ...\Temp\pytest-of-<ユーザー名>` で落ちる → `PYTEST_DEBUG_TEMPROOT` を別のフォルダにする。
- uv が既定の AppData の場所で壊れる → `UV_CACHE_DIR=~/.cache/uv`、`UV_PYTHON_INSTALL_DIR=~/.local/uv-python`、
  `UV_PYTHON_PREFERENCE=only-managed` を設定する（新しい PC で問題がなければ不要）。

## 4. git に入っていないもの（旧 PC にだけある）

| もの | 旧 PC の場所 | 新しい PC で |
| --- | --- | --- |
| MaleCNS v1.0 の生データ（約 1.1 GB、3 ファイル） | `C:\Users\lingm\dev\tsuyulabo-agents\W3-malecns\data\raw\malecns-v1.0\` | **ふだんは不要**。加工済みの回路（約 990 KB）は git に入っている。回路を作り直すときだけ、[公式](https://male-cns.janelia.org/download/)から v1.0（minconf 0.5）の `body-annotations`・`body-neurotransmitters`・`connectome-weights` の Feather を落として、リポジトリ直下の `data/raw/malecns-v1.0/` に置く。手順は [services/brain/README.md](../services/brain/README.md#reproduce-ingestion-and-evaluation) |
| Vercel のリンク（`.vercel/`、`.env.local`） | リポジトリ直下 | `vercel link --yes --project tsuyulabo`。`.gitignore` が書き換わったら `git checkout .gitignore` で戻す |
| Codex のクローン（`~/dev/tsuyulabo-agents/*`） | `C:\Users\lingm\dev\tsuyulabo-agents\` | 不要（全部マージ済み）。`run-codex.sh` が必要なときに作る |
| Claude Code のメモリ | `~/.claude/` | 引き継がれない。大事な方針は下の「5」に書いた |

秘密の値（API キーなど）はリポジトリにも旧 PC にも置いていない。

## 5. 開発の進め方（オーナーの方針）

- **アトミックコミットを徹底**。1 コミット = 1 つの変更。細かく、たくさん（[AGENTS.md](../AGENTS.md)）。
- **学校のメールアドレスは絶対に出さない**（上の「0」）。
- **Claude は指揮官とデザイナー、実装は Codex と Antigravity**。タスクの指示は `docs/agent-tasks/<task>.md` に書いて
  コミットしてから投げる。Codex は上限が 10% 以下になったら使用量リセットを使ってよい（2026-10-01 オーナー）。
- **Codex と Claude の使用量を見ながら進める**（Claude には 5 時間ごとの上限がある）。Codex のモデルは作業の重さで選ぶ:
  - `gpt-6-luna`: 簡単な作業、機械的な作業
  - `gpt-6.1-sol`（既定）: ふつうの機能
  - `gpt-6-astra`: 難しい研究だけ（例: デコーダー改善）
  - reasoning effort の既定は medium
- Codex はサンドボックス（workspace-write）で動かす。サンドボックスを外す設定は使わない。

Codex の動かし方（Git Bash、本体リポジトリで）:

```bash
scripts/agents/run-codex.sh <task> <branch> [effort] [model]
python scripts/agents/apply-commit-plan.py ~/dev/tsuyulabo-agents/<task>
git fetch ~/dev/tsuyulabo-agents/<task> <branch>
git merge --no-ff FETCH_HEAD -m "merge: <内容> (<task>)"
git push
```

- クローンの置き場所は `AGENTS_DIR`（既定 `~/dev/tsuyulabo-agents`、OneDrive の外）、uv は `UV_BIN`（既定は PATH 上の uv）で変えられる。
- Codex はサンドボックスの中では `.git` に書けないので、コミットせずに `.codex-runs/commits.jsonl` に計画を書く。
  それを `apply-commit-plan.py` がアトミックコミットにする。
- 並列ブランチで Alembic のマイグレーションを足すときは、番号がぶつからないように指示で決めておく（マージ時に付け替える）。

## 6. 公開しているもの

| もの | 場所 | 更新のしかた |
| --- | --- | --- |
| Web の公開デモ | https://tsuyulabo.vercel.app | リポジトリ直下で `vercel deploy --prod --yes`（プロジェクト `tsuyulabo`、Root Directory `apps/web`、`NEXT_PUBLIC_DEV_TOOLS=0`、API の URL なし＝デモモード）。Git Bash で `vercel api` を使うときは `MSYS_NO_PATHCONV=1` |
| Android アルファ（APK） | [v0.1.0-alpha.1](https://github.com/lingmulongtai/tsuyulabo/releases/tag/v0.1.0-alpha.1) | `docs/releases/<tag>.md` を書いてから `v0.1.0-alpha.N` タグを push → `android.yml` がプレリリースを作る |
| API | オーナーの PC（`https://ozg14.tail4204cd.ts.net`、Web からは Vercel が転送） | `scripts/selfhost/deploy.ps1`（[selfhost.md](selfhost.md)）。Cloud Run の手順は [deploy.md](deploy.md) に残してある |
