# ゲーム API 仕様（v1）

FastAPI。ベースパス `/v1`。OpenAPI は `/openapi.json`（Web の型はここから生成する）。

## 原則

- **サーバーが正しさを決める**: 時刻、採点、報酬、通貨、乱数はすべてサーバー。
- **冪等性**: 状態を変える `POST` / `PUT` / `PATCH` / `DELETE` はすべて `Idempotency-Key` ヘッダー（UUID）必須。同じユーザー・同じキー・同じリクエストの再送には、保存しておいた最初のレスポンス（ステータスとボディ）をそのまま返す。メソッド、パス、クエリ文字列、本文のバイト列のいずれかが違う場合は 409 `idempotency_key_reused`。キーの保持はサーバー実時刻で 24 時間。
- **入力制限**: 更新リクエストの本文は 64 KiB まで（超過は 413 `payload_too_large`）。チャンク転送でも受信中に制限する。JSON の NaN / Infinity / 数値オーバーフローは 422 `validation_error`。
- **台帳**: 通貨の増減は `ledger_entries` に複式で記録（`user:<id>:shizuku` と `system:rewards` など）。残高は `ledger_accounts.balance` にキャッシュし、台帳と一致することをテストで保証。
- **遅延評価**: ステータスの減少、ケアミス、採集は読み出し時に「前回計算した時刻」から「今」までをまとめて計算して保存する。
- **エラー形式**:

```json
{ "error": { "code": "slot_already_used", "message": "この時間帯のごはんはもう作りました", "details": {} } }
```

主なコード: `unauthorized`, `validation_error`, `not_found`, `idempotency_key_required`, `no_active_week`, `week_already_active`, `slot_already_used`, `daily_limit_reached`, `not_available_today`, `puzzle_expired`, `puzzle_already_submitted`, `invalid_submission`, `insufficient_funds`, `team_full`, `level_cap_reached`, `friend_limit`, `already_friends`, `dev_tools_disabled`.

## 認証（アルファ）

- `POST /v1/auth/guest` → ゲストユーザーを作り、JWT（HS256、`sub` = user_id、有効期限 90 日）を返す。
- 以降は `Authorization: Bearer <token>`。
- 本番では API と worker に `TSUYU_ENV=production` と、ランダムに生成した 32 バイト以上の `JWT_SECRET` を設定する。短い値や既定の開発用シークレットでは起動を拒否する。`TSUYU_ENV` は `development`（既定）、`test`、`production` のいずれか。
- 本番では Supabase Auth / Firebase Auth の ID トークン検証に差し替える（`auth/provider.py` にインターフェースを切る）。

## エンドポイント

### システム

| メソッド | パス | 説明 |
| --- | --- | --- |
| GET | `/healthz` | 死活確認（DB と Redis の疎通も返す） |
| GET | `/v1/clock` | `server_now`, `game_now`, `tz`, `slot`, `day_boundary_hour` |
| GET | `/v1/odds` | 羽化の確率表、大成功・ひらめきの確率（公開用） |

### ユーザー

| メソッド | パス | 説明 |
| --- | --- | --- |
| POST | `/v1/auth/guest` | `{ "display_name": "ゆうき" }` → `{ user, token }` |
| GET | `/v1/me` | プロフィール、フレンドコード、残高、研究ランク |
| PATCH | `/v1/me` | 表示名、称号、自慢の1匹 |

### ホーム（まとめて取得）

`GET /v1/home` → 画面に必要なものを 1 回で返す。

```json
{
  "clock": { "game_now": "...", "slot": "morning", "research_day": 3, "weekday_label": "水" },
  "week": { "id": "...", "research_day": 3, "stage": "larva2", "ready_to_eclose": false, "care_miss": 0, "points_so_far": 5420 },
  "fly": { "stage": "larva2", "hunger": 70, "cleanliness": 45, "mood": 61, "mood_label": "ふつう", "growth": 88.5 },
  "todo": [
    { "action": "meal", "status": "done", "slot": "morning" },
    { "action": "training", "status": "available", "remaining": 2 },
    { "action": "meal", "status": "locked", "slot": "night", "available_at": "...18:00..." },
    { "action": "sleep", "status": "locked", "available_at": "..." }
  ],
  "balances": { "shizuku": 1240, "research_points": 60, "kohaku": 0 },
  "team": { "members": [ ... ], "bag_total": 12, "collectable": true },
  "shiori": { "memo": { "text": "...", "evidence": ["sleep#0021"] } | null }
}
```

### 研究週と育成

| メソッド | パス | 説明 |
| --- | --- | --- |
| POST | `/v1/weeks` | 卵を受け取って週を始める（`parents` を指定すると交配の卵。フェーズ2） |
| GET | `/v1/weeks/current` | 進行中の週の詳細（日ごとの記録を含む） |
| GET | `/v1/weeks/current/presentation` | 研究発表会（7日目 night 以降）。内訳、ランク、報酬 |
| POST | `/v1/weeks/current/eclose` | 羽化。`{ omen_sequence, tier, adult }` を返し、報酬を台帳へ。週を終える |
| GET | `/v1/weeks` | 過去の週の一覧（ランク、羽化した子） |

### パズル

| メソッド | パス | 説明 |
| --- | --- | --- |
| POST | `/v1/puzzles` | `{ "kind": "meal" }` など。回数制限と日付の条件をここで判定。`training` は `cue` と `valence` も渡す |
| POST | `/v1/puzzles/{id}/submit` | 提出。採点、抽選、効果の反映、イベント記録、（しつけなら）脳の学習 |

### 睡眠

| メソッド | パス | 説明 |
| --- | --- | --- |
| POST | `/v1/sleep/start` | おやすみ（night のみ） |
| POST | `/v1/sleep/end` | おはよう（morning のみ）。睡眠時間、ボーナス、げんき回復を返す |

### 成虫・チーム

| メソッド | パス | 説明 |
| --- | --- | --- |
| GET | `/v1/adults` | 飼育室の成虫一覧 |
| GET | `/v1/adults/{id}` | 詳細（素質、特性、サブスキル、好き・苦手、とくいワザ、系統、性別、レベル） |
| POST | `/v1/adults/{id}/level-up` | しずくでレベルを 1 上げる |
| PUT | `/v1/team` | `{ "adult_ids": [...] }`（最大 5） |
| GET | `/v1/team` | チームと袋の中身 |
| POST | `/v1/team/collect` | 袋の中身を受け取る（材料、しずく、経験値） |
| GET | `/v1/inventory` | 材料の数 |

### 図鑑

| メソッド | パス | 説明 |
| --- | --- | --- |
| GET | `/v1/zukan` | 行動図鑑（観察した行動）、系統図鑑（出会った系統）、達成率 |

### フレンド

| メソッド | パス | 説明 |
| --- | --- | --- |
| GET | `/v1/friends` | 一覧 |
| POST | `/v1/friends` | `{ "friend_code": "K7QX2MPA" }` |
| DELETE | `/v1/friends/{user_id}` | 解除 |
| GET | `/v1/friends/{user_id}/lab` | 飼育室をのぞく |
| POST | `/v1/friends/{user_id}/like` | いいね（1日1回） |
| POST | `/v1/friends/{user_id}/gift` | `{ "material": "banana", "amount": 5 }`（1日1回） |
| GET | `/v1/notifications` | お知らせ（「ゆうきさんの子が、にじランクで羽化しました」） |

フレンド飼育室は公開専用の応答を使う。`user` は `id`, `display_name`、成虫は `id`, `name`, `sex`, `strain`, `stars`, `level` のみ。`team` は `members` のみで、各成虫に `slot` を加える。育成中の `week` は `stage`, `research_day`, `fly`、`fly` は `hunger`, `cleanliness`, `mood_label` のみ。採集袋、残高、経験値、好み・遺伝子・脳状態、週 ID、詳細な時刻やケア履歴は公開しない。フレンド関係は本人用の成虫・個体・ジョブ等へのアクセス権を与えない。

### シオリ

| メソッド | パス | 説明 |
| --- | --- | --- |
| GET | `/v1/shiori/memo` | 今朝の観察メモ |
| POST | `/v1/shiori/ask` | `{ "question": "なんでりんご酢から離れるの？" }` → 非同期ジョブ `{ job_id }` |
| GET | `/v1/jobs/{id}` | ジョブの状態と結果（`{ answer, evidence: [...], experiments: [...], cost }`） |

### 脳

| メソッド | パス | 説明 |
| --- | --- | --- |
| GET | `/v1/flies/{id}/behavior` | 今の状態で起きやすい行動（アニメ用。デコーダーの出力と確率） |
| POST | `/v1/flies/{id}/experiments` | コピーで実験（匂いの選択テストなど）→ `{ job_id }` |

### 開発用（`TSUYU_DEV_TOOLS=1` のときだけ。それ以外は 403 `dev_tools_disabled`）

| メソッド | パス | 説明 |
| --- | --- | --- |
| GET | `/v1/dev/time` | 今のオフセット |
| POST | `/v1/dev/time/advance` | `{ "to": "next_slot" \| "next_day" \| "eclosion" }` または `{ "hours": 3 }` |
| POST | `/v1/dev/time/reset` | オフセットを 0 に（育成週・睡眠・いいね・ギフトの記録がある場合、非ゼロのオフセットの巻き戻しは 409 `time_reversed`） |

時刻の前進は正方向のみで、累積オフセットは DB の符号付き 32 ビット整数の範囲内。リセット制限は終了済みの週にも適用し、古い日付の回数制限や交配履歴を再利用させない。やり直す場合は新しい開発用ゲストを使う。

## データモデル（主要テーブル）

- `users`（id, display_name, friend_code, title, favorite_adult_id, dev_time_offset_s, created_at）
- `weeks`（id, user_id, started_at, status `active|eclosed`, rank, points, care_miss, eclosed_at, adult_id）
- `larva_states`（week_id, hunger, cleanliness, growth, hunger_zero_since, last_computed_at, stage）
- `care_events`（id, user_id, week_id, kind, research_day, slot, score, payload JSON, created_at）… 出来事の記録。シオリの根拠 ID になる（表示は `#0412` のような連番 `seq`）
- `puzzles`（id, user_id, week_id, kind, params JSON, secret JSON, issued_at, expires_at, submitted_at, result JSON）
- `adults`（id, user_id, week_id, name, sex, strain, stars, traits JSON, subskills JSON, level, exp, energy, brain_params JSON, learned_weights BYTEA, skills JSON, created_at）
- `team_slots`（user_id, slot 0-4, adult_id, bag JSON, last_computed_at）
- `inventory`（user_id, material, amount）
- `ledger_accounts`（id, owner, currency, balance）/ `ledger_entries`（id, tx_id, account_id, amount, reason, ref, created_at）
- `idempotency_keys`（user_id, key, method, path, status_code, response JSON, created_at）

  `path` はマイグレーションなしでリクエスト識別を強化するため、パス先頭最大 420 文字と `#sha256=<完全なリクエスト識別情報のハッシュ>` を保存する。指紋のない旧レコードは安全に本文を照合できないため、保持期間内の再送を 409 とする。旧版・新版を同時運用しないこと。
- `friendships`（user_id, friend_id, created_at）/ `likes`（from, to, day）/ `gifts`（from, to, material, amount, day）
- `notifications`（id, user_id, kind, payload, created_at, read_at）
- `sleep_sessions`（id, user_id, started_at, ended_at, bonus）
- `shiori_messages`（id, user_id, role, text, evidence JSON, cost JSON, created_at）
- `experiments`（id, user_id, adult_or_week_id, kind, params, result, seq, created_at）… 表示 ID は `#c-19`
- `jobs`（id, user_id, kind, status, result, error, created_at, finished_at）
- `papers`（id, title, authors, year, doi, chunk, embedding vector(384)）… RAG 用（pgvector）

## 脳ジョブとの連携

- `BRAIN_MODE=inline`（テスト・ローカル簡易）: API プロセスで `tsuyu_brain` を直接呼ぶ。
- `BRAIN_MODE=queue`（docker compose / 本番）: Redis（arq）にジョブを積み、`services/worker` が処理。しつけの学習は短いので、提出の応答内で結果を待つ（タイムアウト 3 秒、超えたら「学習中」として後で反映）。
