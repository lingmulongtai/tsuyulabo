# ツユラボ 開発計画（Phase 1 → アルファ版）

企画書: [docs/spec/kikakusho-v0.2.html](spec/kikakusho-v0.2.html)（テキスト版: [kikakusho-v0.2.txt](spec/kikakusho-v0.2.txt)）

このファイルは「どう作るか」の地図。進捗と引き継ぎは [HANDOFF.md](HANDOFF.md) に書く。

## ゴール（アルファ版）

企画書の「フェーズ1 ポートフォリオ版」のうち、**1週間を最後まで遊べる**ところまでを、企画書どおりのフルスタック構成で作る。

- 1週間の育成（卵 → 幼虫 → さなぎ → 成虫）と研究発表会
- ごはんづくり（ブロックパズル）、しつけ（回路パズル）、そうじ、温度あわせ、さなぎの場所えらび
- 羽化の演出と、素質・特性・性別・突然変異
- 研究チームの採集とレベル
- 行動図鑑、シオリ（朝のメモ、発表会、なんで？）
- フレンド（追加、飼育室を見る、いいね、おすそわけ）
- 脳エンジン、行動デコーダー、評価を CI に
- デバッグ用の時間スキップ（開発環境のみ）で、1週間を数分で通しプレイできる

## 技術スタック

| 層 | 技術 | 場所 |
| --- | --- | --- |
| Web アプリ | Next.js (App Router) + TypeScript + React、演出は PixiJS、音は Web Audio、PWA | `apps/web` |
| ゲーム API | FastAPI + SQLAlchemy 2 (async) + Alembic + Pydantic v2 | `services/api` |
| 脳エンジン | PyTorch で書いた LIF スパイキングネット、学習則、個体差、行動デコーダー | `services/brain` |
| シオリ | 自作エージェント（LLM ゲートウェイ、ツール、根拠 ID 検証、RAG） | `services/shiori` |
| ワーカー | arq（Redis キュー）: 脳ジョブ、シオリジョブ、定期ジョブ | `services/worker` |
| DB | Postgres 16 + pgvector（テストは SQLite） | docker compose |
| キャッシュ/キュー | Redis 7 | docker compose |
| CI | GitHub Actions: 型チェック、テスト、脳テスト、AI 評価、Playwright | `.github/workflows` |

Python は **uv workspace**（ルートの `pyproject.toml`）、Node は **npm workspaces**（ルートの `package.json`）。

## リポジトリ構成

```
tsuyulabo/
├─ apps/web/                 Next.js（画面・演出・パズルのクライアント実装）
├─ services/api/             FastAPI（正しさはすべてここで決める）
│   └─ src/tsuyulabo_api/
│       ├─ domain/           純粋なゲームルール（DB を知らない。テストしやすい）
│       ├─ db/               SQLAlchemy モデル、セッション
│       ├─ routers/          HTTP エンドポイント
│       └─ services/         domain と db をつなぐ処理（台帳、時計、冪等性…）
├─ services/brain/           tsuyu_brain（PyTorch の脳エンジン）
├─ services/shiori/          tsuyu_shiori（研究員シオリのエージェント）
├─ services/worker/          tsuyu_worker（arq ワーカー）
├─ packages/fixtures/        Python と TypeScript で共有するゴールデンテスト（JSON）
├─ docs/                     企画書、この計画、仕様、引き継ぎ
└─ docker-compose.yml
```

## 仕様（実装の正）

- [specs/game-rules.md](specs/game-rules.md) … 1週間のスケジュール、ステータス、ケアミス、発表会、羽化、チーム、レベルの数値
- [specs/puzzles.md](specs/puzzles.md) … 各ミニゲームの問題データ・操作記録・採点（サーバーとクライアントの共通契約）
- [specs/api.md](specs/api.md) … REST エンドポイント、認証、冪等性、エラー形式
- [specs/brain.md](specs/brain.md) … 脳エンジン、回路、学習則、個体差、デコーダー、評価
- [specs/shiori.md](specs/shiori.md) … シオリのエージェント設計と評価

数値はアルファ用の仮決め。調整したら仕様の方を先に直す。

## 進め方（ウェーブ）

| ウェーブ | 内容 | 担当 |
| --- | --- | --- |
| W0 | リポジトリ、計画、仕様、土台（uv / npm workspaces、Next.js 雛形、FastAPI 雛形） | Claude |
| W1 | 脳エンジン / ゲームルール（domain）/ API の土台（DB・認証・時計・冪等性・台帳）/ パズルの TS エンジン / デザインシステムとキャラ | Codex ×4 並列 + Claude（デザイン） |
| W2 | ゲーム API（domain + DB + 脳）/ ワーカーとシオリ / docker compose と CI / API クライアントと画面 | Codex ×3 並列 + Claude（画面） |
| W3 | フレンド、図鑑、チーム画面、羽化と発表会の演出、音、E2E、デプロイ | Codex + Claude |

## 役割分担

- **Claude（指揮 + デザイン）**: 仕様を書く、タスクを切って Codex に渡す、レビューとマージ、デザインシステム、キャラクター（企画書の SVG を React 化）、画面の見た目と演出。
- **Codex（実装）**: 仕様どおりのロジック、API、脳エンジン、テスト、インフラ。1タスク = 1ブランチ = 1クローン（`C:\Users\lingm\dev\tsuyulabo-agents\<task>`）で並列に動かす。

## コミットのルール（重要）

- **アトミックコミットを徹底**。1コミット = 1つの意味のある変更。迷ったら分ける。
- Conventional Commits（`feat(api): ...`, `test(brain): ...`, `docs: ...`, `chore(web): ...`）。
- テストはそれを通す実装と同じコミットか、直後のコミットに入れる。壊れた状態のコミットを作らない。
- 生成物（lockfile 以外のビルド成果物）はコミットしない。

## ローカルで動かす（W2 以降）

```bash
docker compose up        # web, api, worker, postgres, redis
```

個別に:

```bash
uv sync                  # Python の依存
uv run pytest            # Python テスト
npm install              # Node の依存
npm run dev -w apps/web  # Web
```
