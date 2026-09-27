# ミニゲーム（パズル）仕様

サーバーが問題（`params`）を出し、クライアントは遊んだ**操作の記録**（`submission`）を送る。サーバーが同じルールで再生して採点する。クライアントの採点は表示用。

- Python 実装: `services/api/src/tsuyulabo_api/domain/puzzles/`
- TypeScript 実装: `apps/web/src/game/puzzles/`
- 共有ゴールデンテスト: `packages/fixtures/puzzles/<kind>/*.json`（形式は最後に記載）。Python 側が生成し、両方のテストが読む。

## 共通

- 問題は `POST /v1/puzzles` で発行。`puzzle_id`（UUID）、`kind`、`params`、`issued_at`、`expires_at`（発行から 10 分）を返す。
- `POST /v1/puzzles/{puzzle_id}/submit` で提出。**有効な提出は 1 回だけ**。無効な提出（ルール違反）は 422 を返し、問題は開いたまま。
- 時刻 `t` はすべて「クライアントが遊び始めてからのミリ秒」。単調非減少であること。
- ずる対策: サーバーの壁時計で `submit時刻 - issued_at >= 最後の t - 2000ms` を満たさない提出は無効（実時間より速く遊んだことになる）。
- 乱数は Python の `random.Random(seed)`。`seed` はサーバーだけが持ち、`params` には入れない（問題の中身そのものを渡す）。

## 1. ごはんづくり `meal`（ブロックパズル、30秒）

### params

```json
{
  "rows": 8, "cols": 8,
  "time_limit_ms": 30000,
  "hand_size": 3,
  "theme": "banana",
  "pieces": [ { "shape": "l3a", "ingredient": "banana" }, ... 90 個 ]
}
```

- 材料 `ingredient`: `banana`, `apple`, `grape`, `yeast`, `agar`。`theme` はこの中から 1 つ（研究所のおてんき）。
- 形 `shape`（回転なし。オフセットは `[dr, dc]`、左上が `[0,0]`）:

| id | セル |
| --- | --- |
| `m1` | `[0,0]` |
| `d2h` | `[0,0] [0,1]` |
| `d2v` | `[0,0] [1,0]` |
| `i3h` | `[0,0] [0,1] [0,2]` |
| `i3v` | `[0,0] [1,0] [2,0]` |
| `l3a` | `[0,0] [1,0] [1,1]` |
| `l3b` | `[0,0] [0,1] [1,0]` |
| `l3c` | `[0,0] [0,1] [1,1]` |
| `l3d` | `[0,1] [1,0] [1,1]` |
| `o4` | `[0,0] [0,1] [1,0] [1,1]` |
| `i4h` | `[0,0] [0,1] [0,2] [0,3]` |
| `i4v` | `[0,0] [1,0] [2,0] [3,0]` |
| `t4` | `[0,0] [0,1] [0,2] [1,1]` |
| `l4` | `[0,0] [1,0] [2,0] [2,1]` |
| `s4` | `[0,1] [0,2] [1,0] [1,1]` |
| `i5h` | `[0,0] … [0,4]` |
| `i5v` | `[0,0] … [4,0]` |
| `o9` | 3×3 全部 |

- 生成時の重み: `m1` 4, `d2h/d2v` 各 4, `i3h/i3v` 各 3, `l3a..d` 各 3, `o4` 3, `i4h/i4v` 各 2, `t4` 2, `l4` 2, `s4` 2, `i5h/i5v` 各 1, `o9` 1。材料は theme が 30%、残り 4 種が 17.5% ずつ。

### 手札

- `pieces` を先頭から 3 個ずつ配る。手札 k = `pieces[3k .. 3k+2]`。
- 手札の 3 個は好きな順に置ける。3 個とも置いたら次の 3 個が配られる。

### submission

```json
{ "moves": [ { "p": 0, "r": 3, "c": 2, "t": 1840 }, ... ], "elapsed_ms": 30000 }
```

- `p` は `pieces` の添字。今の手札に含まれ、まだ置いていないこと。
- 置くセルがすべて盤内かつ空であること。`t <= time_limit_ms + 1500`。

### 検証の順番と細かい決まり

- 最初に `moves` がオブジェクトの配列で、発行した `pieces` の数（通常 90）以下であることを確認（違えば `wrong_length`）。配置を再生する前に、すべての時刻を検証する。
- 時刻の検証順: `elapsed_ms` が非負の整数（違えば `non_monotonic_time`）→ `elapsed_ms <= 600000`（超過は `time_exceeded`）→ 各 `t` が非負の整数かつ単調非減少 → 各 `t <= time_limit_ms + 1500` → 最後の `t <= elapsed_ms`。時刻の不正は `non_monotonic_time`、上限超過は `time_exceeded`。同時刻の手は許可する。
- 各手は `p` の整数判定（`not_in_hand`）→ 使用済み（`already_placed`）→ 現在の手札（`not_in_hand`）→ `r, c` の整数判定と全セルの範囲（`out_of_bounds`）→ 占有（`cell_occupied`）の順。最初の違反を返す。
- 時刻の上限は境界を含む。得点の丸めは下記の `floor(line_score * multiplier)` のみで、浮動小数点の許容誤差は加えない。

### 置いたあとの処理と採点

1. ピースのセルに材料を置く。
2. 埋まった行と列を**同時に**判定し、すべて消す（交差セルは 1 回だけ数える）。
3. 採点（1 手ごと）:
   - `cells` = ピースのセル数
   - `L` = 消えた行 + 列の本数
   - `line_score` = `100 * L * (L + 1) / 2`（1本 100, 2本 300, 3本 600, 4本 1000 …）
   - `combo`: 1 本以上消した手が続いた回数（最初の消去で 1）。何も消さない手で 0 に戻る。
   - `multiplier` = `1 + 0.5 * (combo - 1)`（消去がない手では 0 扱いで line_score も 0）
   - `theme_bonus` = 消えたセルのうち材料が `theme` のもの × 15
   - `move_score` = `cells + floor(line_score * multiplier) + theme_bonus`
4. `score` = Σ `move_score`。

### result（サーバー → クライアント）

```json
{ "score": 2480, "lines": 11, "max_combo": 3, "theme_cells": 20,
  "great_success": true, "effects": { "growth": 24.8, "hunger": 60 } }
```

- 大成功の確率 `p = min(0.35, 0.04 + score / 12000) + team_great_bonus`、7日目は `p * 2`、上限 0.6。サーバーが抽選。
- 成長ポイント `growth = score / 100`（`larva3` の日は ×1.5）。大成功で成長ポイントも ×2。

## 2. しつけ `training`（回路つなぎ、5〜20秒）

数字の順に、全部のマスを一筆書きでつなぐ。

### 発行リクエスト（プレイヤーが教える内容を選ぶ）

```json
{ "kind": "training", "cue": "banana", "valence": "reward" }
```

- `cue`: `banana`（バナナの匂い）, `apple_vinegar`（りんご酢の匂い）, `yeast`（酵母の匂い）, `grape`（ぶどうの匂い）, `blue_light`（青い光の合図）
- `valence`: `reward`（あまいごほうび）, `punish`（にがいごはん）

### params

```json
{ "n": 5, "checkpoints": [ { "cell": 0, "k": 1 }, { "cell": 8, "k": 2 }, ... ], "cue": "banana", "valence": "reward" }
```

- マス番号 `cell = r * n + c`。
- `n`: 2〜3日目は 5、4〜7日目は 6。チェックポイント数 `K`: n=5 → 5、n=6 → 7。
- 生成: ランダムなハミルトン路（Warnsdorff 法 + ランダムなタイブレーク + 行き詰まったらやり直し）を作り、`k=1` を先頭、`k=K` を末尾、残りを路の上にほぼ等間隔（±1 のゆらぎ）で置く。解が 1 つとは限らない（どの正しい路でも合格）。

### submission

```json
{ "path": [0, 1, 6, 5, ...], "elapsed_ms": 9800 }
```

### 判定

- `path` の長さが `n*n`、重複なし、隣り合うマスは上下左右に隣接。
- `path[0]` が `k=1` のマス、最後が `k=K` のマス、チェックポイントのマスが `k` の昇順に現れる。
- ★: `s = n*n / 25` として、`elapsed_ms < 12000*s` → 3、`< 25000*s` → 2、それ以外 → 1。
- API の最終的な星判定には `max(申告 elapsed_ms, floor((サーバー提出時刻 - issued_at) * 1000))` を使う。申告時間を短く偽っても星や学習量を増やせない。共通の壁時計検証は元の申告値に対して行う。端末内のプレビューは申告時間による暫定値で、発行後の待ち時間と通信時間を含むサーバー判定を優先する。

### 検証の順番と細かい決まり

- `path` が配列で長さ `n*n`（`wrong_length`）→ 全セルが整数かつ盤内（`out_of_bounds`）→ 重複（`revisit`）→ 全区間の上下左右の隣接（`not_adjacent`）→ 始点（`bad_start`）→ 終点（`bad_end`）→ チェックポイント順（`checkpoint_order`）→ 時刻、の順で最初の違反を返す。
- チェックポイントは `k` の昇順に並べて比較する。時刻は `elapsed_ms` が非負の整数でなければ `non_monotonic_time`、`600000` を超えれば `time_exceeded`。`600000` 自体は許可し、独自の短い制限時間は設けない。
- 星の境界は上記の厳密な `<`。丸めや許容誤差は加えない。

### result

```json
{ "stars": 3, "hirameki": false, "learning_strength": 0.36, "skill_unlocked": null,
  "association": { "cue": "banana", "valence": "reward", "value": 0.52 } }
```

- ひらめき: 10%（★3 なら 15%）。学習の強さ `learning_strength = stars * 0.12`、ひらめきで ×2。
- `association.value` は脳エンジンで学習したあとの好み（-1 苦手 〜 +1 好き）。
- とくいワザ: 好みの絶対値が 0.6 を超えたら解放（`banana` 好き → `banana_search` 「バナナさがし」など。一覧は `domain/constants.py`）。

## 3. そうじ `cleaning`（タイミング、5秒）

びんをトントンと 3 回叩く。

### params

```json
{ "period_ms": 1400, "taps": 3, "zone": { "center": 0.5, "perfect": 0.06, "good": 0.15 }, "phase": 0.27 }
```

- `period_ms`: 2日目 1400、3日目 1300、4日目 1200、5日目 1100。
- マーカー位置（0〜1 の三角波）: `u = (t / period_ms + phase) mod 1`、`x = u < 0.5 ? 2u : 2 - 2u`。

### submission

```json
{ "taps": [820, 1650, 2430], "elapsed_ms": 2500 }
```

- ちょうど `taps` 回、狭義単調増加、`t <= 10000`。

### 採点

- 各タップ: `d = |x(t) - center|`。`d <= perfect` → perfect 34 点、`d <= good` → good 22 点、それ以外 miss 5 点。
- `score = min(100, 合計)`。`grades: ["perfect", "good", "miss"]` も返す。

### 検証の順番と細かい決まり

- `taps` が配列で指定回数（`wrong_tap_count`）→ `elapsed_ms` が非負の整数（`non_monotonic_time`）→ `elapsed_ms <= 600000`（`time_exceeded`）→ 各タップの時刻 → 最後のタップが `elapsed_ms` 以下（`non_monotonic_time`）の順。
- 各タップは、非負の整数かつ狭義単調増加（違えば `non_monotonic_time`）を先に調べ、次に `t <= 10000`（超過は `time_exceeded`）を調べる。最初の `t=0` と上限ちょうどは許可する。
- 境界を含む判定を浮動小数点誤差から守るため、実際の比較は `d <= perfect + 1e-12`、次に `d <= good + 1e-12` とする。得点は整数の合計を 100 で打ち切り、追加の丸めはしない。

## 4. 温度あわせ `temperature`（5秒）

ゆれる針を 25℃ 付近で止める。

### params

```json
{ "period_ms": 1600, "center_c": 25.0, "amp_c": 7.0, "phase": 0.61 }
```

- 針の温度: `temp(t) = center_c + amp_c * sin(2π * (t / period_ms + phase))`。

### submission

```json
{ "stop_ms": 2210, "elapsed_ms": 2210 }
```

### 採点

- `score = max(0, round(100 - |temp - 25| * 20))`。`grade`: 90 以上 perfect、60 以上 good、それ未満 miss。

### 検証の順番と細かい決まり

- `elapsed_ms` が非負の整数（`non_monotonic_time`）→ `elapsed_ms <= 600000`（`time_exceeded`）→ `stop_ms` が非負の整数（`non_monotonic_time`）→ `stop_ms <= 600000`（`time_exceeded`）→ `stop_ms <= elapsed_ms`（`non_monotonic_time`）の順で最初の違反を返す。小数の時刻は切り捨てず拒否する。
- 上限 `600000` は境界を含む。5 秒の独自上限は設けない。サーバーの壁時計による期限・不正検出は別途行う（発行から実時間で 600000 ms 以上なら期限切れ）。
- 丸めは `raw = 100 - |temp - 25| * 20` に対して `score = max(0, floor(raw + 0.5))`。正のちょうど半分は上へ丸める（例: 92.5 → 93）。偶数丸めや epsilon は使わない。丸めた得点を 90 以上、60 以上の順に比較する。

## 5. さなぎの場所えらび `pupation_site`（10秒）

### params

```json
{ "options": [
    { "id": "a", "label": "びんの壁の上のほう", "detail": "乾いていて、えさから遠い" },
    { "id": "b", "label": "えさの表面", "detail": "しめっていて、やわらかい" },
    { "id": "c", "label": "ふたのすぐ下", "detail": "明るくて、風が通る" } ],
  "hint": "本物の3齢幼虫は、えさから離れた乾いた場所でさなぎになることが多いよ。" }
```

- 当たりはサーバーだけが知る。シオリのヒントは 70% の確率で当たりを指す内容、30% で別の候補を指す。
- 候補の並びと文言は毎回シャッフル（文言のプールは `domain/constants.py`）。

### submission / result

```json
{ "choice": "a" }
```

```json
{ "hit": true, "effects": { "eclosion_bonus": true } }
```

## 6. 今日の回路 `daily-circuit`（フェーズ2）

- §2 の生成・経路検証を再利用する **7×7、9チェックポイント**の共通問題。育成週やしつけの回数・学習には影響しない。
- 日付はサーバー実時刻の JST 04:00 区切り（03:59 までは前日）。個人の開発用時刻オフセットは使わない。
- `seed = int.from_bytes(SHA-256(UTF-8("daily-circuit:" + YYYY-MM-DD)), "big")` を `random.Random` に渡す。Python のプロセス依存 `hash()` は使わない。全員に同じ盤面を返す。
- `GET /v1/daily-circuit` は `day`, `params`（TrainingParams と同形）, `server_now`, `resets_at`, `attempt`（未開始は null）, `my_result`（未記録は null）を返す。読み出しで計測は開始しない。
- `POST /v1/daily-circuit/start`（`{day}`、Idempotency-Key 必須）でその日の本番を開始。ユーザーと日付ごとに1件。再度の開始は同じ `started_at` / `expires_at` を返し、計測をリセットしない。期限は開始10分後または翌04:00の早い方。
- `POST /v1/daily-circuit/submit` は `{day, path, elapsed_ms}`（Idempotency-Key 必須）。本番開始済みで期限内の完全な経路だけを受理し、共通の壁時計検証も行う。無効な提出は422、期限切れ・日付不一致は409。
- 記録タイムは `max(elapsed_ms, floor((submit時刻 - started_at) * 1000))`。端末から短いタイムを送ってもサーバー経過時間より短くならない。完成時に自動送信し、通信時間も含む。
- 1日1回だけ有効タイムと報酬を確定。同じキーは同じ応答、別キーの再提出も保存済みの結果を返す。期限切れの本番は再開不可。練習はいつでも何度でも可能で、提出・記録更新・報酬なし。
- 報酬は記録タイム **20,000ms未満: 60しずく、40,000ms未満: 40しずく、それ以外: 20しずく**。結果と台帳の複式記録を同一トランザクションで保存。
- `GET /v1/daily-circuit/ranking` は当日の自分と現在のフレンドの有効記録のみ。各人唯一の有効記録がベストタイム。タイム昇順、同タイムは提出時刻昇順、両方同じならユーザーID順で順位を確定する。未参加者には順位を付けない。
- ランキングは表示名、自分かどうか、自慢の成虫の系統・性別を返す。未設定は野生型。画面はホームとフレンドから `/daily` に入り、タイマー、結果とフレンド内順位、ランキングを表示する。

## ゴールデンテスト（fixtures）の形式

`packages/fixtures/puzzles/<kind>/<name>.json`

```json
{
  "kind": "meal",
  "description": "2 lines cleared at once with combo",
  "params": { ... },
  "submission": { ... },
  "expected": { "valid": true, "score": 1234, "lines": 2, "max_combo": 1, "theme_cells": 5 }
}
```

- 抽選（大成功、ひらめき、当たり）は fixtures に含めない。決定的な部分（妥当性と得点）だけを比べる。
- 無効な例も入れる（`"expected": { "valid": false, "reason": "cell_occupied" }`）。`reason` の値は両実装で共通:
  `not_in_hand`, `already_placed`, `out_of_bounds`, `cell_occupied`, `time_exceeded`, `non_monotonic_time`,
  `wrong_length`, `not_adjacent`, `revisit`, `bad_start`, `bad_end`, `checkpoint_order`, `wrong_tap_count`.
