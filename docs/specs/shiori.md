# 研究員シオリ仕様（`services/shiori` / パッケージ `tsuyu_shiori`）

企画書「10 研究員シオリ」「11 AIを自分で作る」。フレームワーク（LangChain 等）に頼らず、エージェントのループ・ツール・根拠検証を自分で書く。

## 役割

| 機能 | いつ | 入力 | 出力 |
| --- | --- | --- | --- |
| 朝の観察メモ | おはようのとき（夜間にまとめて作ってもよい） | 前夜の睡眠、前日のお世話の記録 | 2〜3 文のメモ + 根拠 ID |
| しつけのコーチ | しつけ画面を開いたとき | 今週の記録、好みの状態 | 1 文のアドバイス |
| 研究発表会の司会 | 発表会 | 1週間の記録、ランク | ふり返りの文章 |
| 「なんで？」 | プレイヤーの質問 | 質問、記録、脳の実験 | 根拠つきの答え |
| 図鑑の解説 | 図鑑 | 行動・系統 | 短い解説（事前生成でよい） |

## シオリの約束（コードで守る）

1. ツユの気持ちを代弁しない。「悲しんでいます」ではなく「動きが減っています」。→ 禁止表現リストで出力を検査し、引っかかったら書き直し。
2. **すべての説明に記録か実験の ID をつける**。実在しない ID を含む文は表示しない。→ 出力を文に分け、各文の ID（`#0412`、`#c-19` 形式）をデータベースと照合。ID がない文、存在しない ID の文は捨てる。捨てた数を記録（根拠の検証率）。
3. 実験はいつもコピーで。本物のツユの状態は変えない。→ 実験ツールは状態のコピーを受け取り、書き込みしない。
4. シオリ自身が AI であることを隠さない。→ UI に常に「AI」バッジ。答えの下に「ゲーム内のモデルで測った結果です」。

## 構成

- `gateway/`: LLM ゲートウェイ。`Provider` インターフェース（`complete(messages, tools, model) -> Response`）。
  - `MockProvider`（既定。テンプレートと記録から決定的に文章を作る。API キーなしで全部動く）
  - `AnthropicProvider`、`OpenAIProvider`（`httpx` で直接叩く。キーは環境変数 `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`）
  - `OllamaProvider`（`SHIORI_PROVIDER=ollama` を明示したときだけ。ホストPCの
    `/api/chat` を使い、APIキー不要。既定は引き続き `mock`）
  - モデルの使い分け: 質問応答 = 中くらいのモデル、夜の日誌 = 軽いモデル。応答キャッシュ（同じ入力 → 同じ出力、Redis またはメモリ）。
  - 呼び出しごとにトークン数と概算コストを記録。
- `agent/`: ツール呼び出しのループ（最大 4 ステップ）。
- `tools/`: `get_care_events(week_id, kinds?, research_day?, cue?, valence?)`、
  `count_care_events(week_id, kinds?, research_day?, cue?, valence?)`、
  `get_association(fly_id, cue)`、`run_odor_choice(fly_id, cue, trials=20, seed=0)`、
  `search_papers(query, k)`。実験の状態ロード・コピーはホストのLabが行う。

### 記録ツールの契約（W10）

絞り込みは `RecordStore.care_events(week_id)` と `sleep_sessions(week_id)` の取得後、
ツール層で行う。API側のDBストアのインターフェースは変えない。朝のメモの期間制限も両ツールに適用する。
朝の睡眠は前日正午以降・メモ作成時刻より前に開始した記録に限り、未来の睡眠を参照しない。
指定条件はAND。`kinds`省略は睡眠を含む全種類、空配列は0件。
`research_day`は1〜7の整数で記録のdata.research_dayと一致させる（欠落した記録は一致しない）。
`cue`、`valence`はenumで、ツールスキーマに日本語対応を記載する:
バナナ=banana、りんご酢=apple_vinegar、イースト=yeast、ぶどう=grape、青い光=blue_light;
報酬=reward、罰=punish。`kinds`はtraining / meal / cleaning / temperature /
pupation_site / eclosion / presentation / sleep等の記録種類で、匂いや報酬ではない。

`get_care_events`は `records`、`sleep_sessions`、`total`、`truncated` を返す。
2つの配列は**合計最大20件**、日時の新しい順（日時なしは最後、同日時は数値ID降順、
それ以外はストアからの取得順の逆順）。`total`は条件に一致した上限適用前の全件数、
`truncated`は20件を超えたかどうか。睡眠だけを調べる場合は `kinds=["sleep"]` を指定する。
各レコードは `id`、`kind`、`research_day`、`data`。日時があれば `occurred_at` も返す。
`data`はcue / valence / value / score / great_success / traits / rank / hoursの存在する
項目だけを含み、内部payload・week_id・fly_id等は省く。記録のコピーでありストアを変更しない。

`count_care_events`は同じ条件で、上限適用前にコードで数えた `count`、最大4件の `ids`、
`filters`（week_idと全4条件、省略条件はnull）を返す。0件の場合のidsは同じ期間に確認した
記録から選び、**一致する記録のIDではない**。期間内に記録がなければ空配列。捏造IDは作らない。
エージェントは返されたidsだけを引用可能な根拠に加える。モデルに一覧を数え直させない。

プロンプトは4つの約束と取得・引用の原則を守り、一般の質問に自然に答える。
固定回答テンプレートは置かず、回数と「なんで？」の短い使用例を各1つだけ示す。
- `verify/`: 根拠 ID の検証、禁止表現の検査。
- `rag/`: 論文の短い要約コーパス（`data/papers.jsonl`、手書きの 20 件程度: ショウジョウバエの嗅覚学習、キノコ体、ジャイアントファイバー、体内時計、コネクトーム）。埋め込みは Postgres の pgvector。テストとモックでは BM25 のメモリ検索。

## 評価

`uv run python -m tsuyu_shiori.eval`

- 育成記録から問題と正解を自動生成（例: 「火曜にりんご酢で罰を何回覚えた？」→ 記録から正解 3）。
- 指標: 正答率、根拠の検証率（捨てられなかった文の割合）、1 回答あたりのコスト。
- MockProvider でも回る（CI は Mock で回す）。

## ローカルLLM（Ollama）

`OLLAMA_BASE_URL` はホスト実行時 `http://127.0.0.1:11434`、Compose 内では
`http://host.docker.internal:11434`。API と worker は host-gateway を登録する。
QA モデルは `OLLAMA_QA_MODEL`（既定 `qwen3.5:4b`）、日誌・朝のメモは
`OLLAMA_JOURNAL_MODEL`（既定 `qwen3.5:2b-q4_K_M`）で自由に変更できる。
将来の LoRA モデルも同じ設定で選ぶ。キャッシュは両方のモデル名で分離する。

全リクエストに `stream=false`、`think=false`、temperature 0.2 と
`OLLAMA_NUM_CTX`（既定8192）を送る。巨大な既定コンテキストによるGPU退避を避ける。
`OLLAMA_KEEP_ALIVE` は既定30m、`OLLAMA_TIMEOUT` は既定120秒。
`OLLAMA_NUM_PREDICT` は正の整数（既定512）で各呼び出しの生成上限を指定し、キャッシュを分離する。
上限到達の呼び出し数も記録する。部分的な本文は通常の検証・空回答回復に従う。
ツール呼び出しを含むネイティブassistantメッセージとツール結果を毎回再送する。
トークンは `prompt_eval_count` / `eval_count` を記録し、金額は0 USDとする。

記録を取得する前の回答は受け入れず、残りステップでツール呼び出しを促す。
get_care_events / count_care_events / get_association / run_odor_choiceの成功はどれも取得として扱う。
論文検索だけや引数エラーは個体の記録取得として扱わない。
検証済み本文が空なら、同じコンテキストと取得済みツール結果を使って Mock で再生成する。
`stopped_reason="fallback"` と `fallback_used=true` を返し、元モデルの検証結果を
`provider_verification` に保持する。Mockも新しい取得・集計契約を使い、切り詰めた一覧を全件として数えない。
根拠が全くない場合だけ `empty_state=true` の記録取得案内を返す。この案内は
個体の説明ではなくUIの状態表示であり、架空の根拠IDや検証成功を付けない。
通常の最大4モデル呼び出しに加え、空回答の回復に限り最大4回のオフラインMock呼び出しを許す。
同じ実験引数の結果を再利用し、実験を重複させない。上記4つの約束は変えない。

評価は `--provider mock|ollama`（既定mock）、`--qa-model`、`--journal-model`、
`--limit N` を受け付ける。実測は `SHIORI_LIVE_EVAL=1` が必要で、CIでは常に禁止。
回数・トピックは文言テンプレートではなく数値、観測内容、IDで採点する。
正答率・検証率・読みやすさはフォールバック前の元モデル出力で計測し、代替回答後の
正答率も別に記録する。既存のMockゲート（回数0.8以上、検証0.95以上、
トピックと読みやすさ1.0）は維持し、open正答率0.7以上を追加する。
評価は回数42問・トピック9問に、好みの理由、睡眠、発表会、最多のしつけ等のopen10問を加える。
openも観測値・行動回数・ランク・ID等を採点し、特定の文言テンプレートを要求しない。
元モデルと代替後のopen正答率を別に記録する。4B実測の目標は回数0.8・トピック0.8・
open0.7・検証0.95以上（Mockの厳しいトピック/読みやすさゲートとは区別）。
入力トークンは1質問の全モデル呼び出しの合計の平均/最大と、1呼び出しの最大を記録する。
コンテキスト上限との直接比較は1呼び出しの値で行い、累積トークンと混同しない。
各回答の遅延、平均/p95、トークン、
フォールバック件数を `eval-results/shiori-<provider>-<model>/` に保存する。
ファイル名ではモデル名の記号をハイフンに変換する。実測レポートは
`services/shiori/reports/local-llm.md`。実測前のデバッグにはlimitを使い、CPU推論は強制しない。

`python -m tsuyu_shiori.eval_memos --provider mock|ollama --journal-model MODEL` は
synthetic weekの3つの朝（9月23・25・28日08:00 JST）のメモを再現する。
QAと同じlive opt-in/CI禁止を適用し、元モデル・代替後本文、検証、遅延、トークンを
`eval-results/shiori-memos.json`（`--output`で変更可能）へ保存する。
