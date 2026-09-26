# 脳エンジン仕様（`services/brain` / パッケージ `tsuyu_brain`）

企画書「11 AIを自分で作る」の 脳エンジン・学習ルール・個体差ジェネレーター・行動デコーダー を作る。PyTorch だけで一から書く（Brian2 などのシミュレータは使わない）。

## 方針

- **配線は共通、個体ごとに持つのは小さな差分だけ**: 回路の重み行列は読み取り専用で全個体共通。1匹ごとに保存するのは「生まれつきのパラメータ（数十個の float）」と「学習で変わった KC→MBON の重み」だけ。
- **部分回路だけ計算する**: 匂い（キノコ体）、摂食、逃避、旋回、身づくろいを別々の小さな回路として持ち、必要なものだけ動かす。
- **決定的**: `seed` を渡せば同じ結果。テストは seed 固定。
- **バッチ**: 試行をバッチ次元に並べて一度に計算（Shiori の「コピーで 20 回試す」を 1 回の forward で）。

## 配線データ

- `connectome/` にバージョン付きで置く（例: `toy-v0`）。
- **アルファは合成配線 `toy-v0`**: 実在のニューロン名と、実際の回路の「形」（どの細胞群がどこへつながるか、興奮か抑制か）に合わせて、細胞数と重みを小さくした合成データ。コードで決定的に生成する（`connectome/toy_v0.py`、seed 固定）。
- **あとで本物に置き換える**: `scripts/ingest_malecns.py` を用意し、MaleCNS v1.0（CC-BY）の配線を部分回路ごとの疎行列（`.npz`）に前処理できるようにする。データのダウンロードは手動（README に手順と出典を明記）。インターフェースは `toy-v0` と同じ `Circuit` を返す。

## ニューロンモデル

- 電流ベースのシナプスをもつ LIF（leaky integrate-and-fire）。
  - `tau_m = 20ms`, `tau_syn = 5ms`, `v_rest = 0`, `v_th = 1.0`（個体差で変わる）, `v_reset = 0`, 不応期 2ms。
  - `dt = 0.5ms`。
- 入力: ポアソンスパイク列（刺激の強さ → 発火率）。
- 出力: 各ニューロンのスパイク列と、窓ごとの発火率。
- 実装: `torch` のテンソル演算（重みは dense か `torch.sparse`、どちらでも。細胞数は各回路 数十〜数百）。

## 回路（toy-v0）

| 回路 id | 細胞群（実名に合わせる） | 役割 |
| --- | --- | --- |
| `olfaction_mb` | ORN（8 糸球体: `banana`=酢酸イソアミル, `apple_vinegar`=酢酸, `yeast`=エタノール, `grape`, ほか 4）→ PN（8）→ KC（200、各 KC は PN を 6 本ランダムに受ける）→ APL（全体抑制）→ MBON（`MBON_ap` 近づく / `MBON_av` 離れる）。DAN（`PAM` ごほうび、`PPL1` 罰）が KC→MBON を変える | 匂いの好き・苦手 |
| `feeding` | 糖 GRN（Gr64f）→ 介在 → `MN9`（口吻を伸ばす運動ニューロン）。苦味 GRN（Gr66a）が抑制 | 食べる |
| `escape` | `LPLC2` / `LC4`（迫ってくる影）→ `DNp01`（ジャイアントファイバー）→ 逃げる | 逃避 |
| `steering` | 左右の光受容体 → 左右の `DNa02` → 旋回。歩行 DN（自発発火あり） | 歩く・曲がる・光に向かう |
| `grooming` | 触角の機械受容（JO）→ `aDN` → 前脚の身づくろい | 身づくろい（前脚をこするポーズ） |
| `blue_light` 合図 | 視覚 → KC の一部（視覚 KC）に入力 | 光の合図の学習 |

## 学習ルール（キノコ体）

- しつけ 1 回 = 「合図（cue）を出しながら、DAN を鳴らす」。
- `valence = reward` → `PAM` が発火 → **KC→`MBON_av` を弱める**（離れる力が減る → 近づく）。
- `valence = punish` → `PPL1` が発火 → **KC→`MBON_ap` を弱める**。
- 更新: `ΔW[kc, mbon] = -η * learning_strength * trace_kc * dan_activity`（重みは 0 以上でクリップ）。`learning_strength` はパズルの★から来る（puzzles.md）。
- 好みの指標: 匂いを出したときの `PI = (rate(MBON_ap) - rate(MBON_av)) / (rate(MBON_ap) + rate(MBON_av) + ε)`、-1〜+1。
- API: `apply_training(state, cue, valence, strength, seed) -> (new_state, association_value)`。

## 個体差ジェネレーター

- 羽化のときに `generate_individual(traits, sex, seed) -> BrainParams` を呼ぶ。
- `BrainParams`: 各回路のゲインとしきい値、左右の非対称など数十個の float。
- 平均の周りに小さな正規ノイズ（全個体）＋ 特性ごとの決まったずれ（game-rules.md の表）。
- **検証**: 同じ特性を持つ個体群は、同じ向きの行動の偏りを示す（例: `right_turner` の群は右旋回率が有意に高い）。テストで確認。

## 行動デコーダー

- 入力: 出力ニューロン（`MN9`, `DNp01`, 左右 `DNa02`, 歩行 DN, `aDN`, `MBON_ap`, `MBON_av`）の窓ごとの発火率（特徴量）。
- 出力ラベル: `rest`, `walk`, `turn_left`, `turn_right`, `feed`, `escape`, `groom`, `approach`, `avoid`。
- 学習データは自分で作る: 刺激シナリオ（無刺激、糖、苦味、影、左右の光、触角刺激、好き/苦手な匂い）を個体差つきで大量にシミュレーションし、シナリオから決まるラベルをつける。
- モデル: まず自作のロジスティック回帰（多クラス、`torch` で勾配降下）→ 小さな MLP。
- アプリでは `GET /v1/flies/{id}/behavior` でアニメーションの選択に使う。

## 評価（CI で自動）

`uv run python -m tsuyu_brain.eval` が JSON と Markdown の表を `eval-results/brain/` に出す。

| テスト | 合格条件 |
| --- | --- |
| 糖 → `MN9` | 糖刺激で `MN9` の発火率が無刺激の 5 倍以上 |
| 影 → `DNp01` | 迫る影で `DNp01` が発火、無刺激では発火しない |
| 苦味で摂食が止まる | 糖+苦味で `MN9` の発火率が糖のみの 50% 未満 |
| しつけで好みが変わる | バナナ+ごほうびを 3 回 → バナナの PI が +0.3 以上上がる。罰なら下がる |
| 特性が行動に出る | `right_turner` 群の右旋回率 > 野生型群（片側検定 p < 0.01） |
| デコーダーの正解率 | 本物の配線で 85% 以上。配線をシャッフルした対照では大きく下がる（差を表に出す） |

pytest の単体テストは `services/brain/tests/`。評価は重いので `-m eval` マーカーで分ける。
