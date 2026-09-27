# ツユラボの公開手順（Vercel / Cloud Run）

まず Web だけを公開できます。バックエンドの準備後、同じ Vercel プロジェクトに API URL を設定して再公開します。このリポジトリの設定追加だけではデプロイされません。以下の `--execute`、`deploy --prod`、Actions の **Run workflow** はオーナーが実行してください。

## 1. Web の公開デモを先に出す

必要なもの: Node.js 22、Vercel アカウント。以下の PowerShell コマンドはすべて**リポジトリのルート**で実行します。`apps/web` に移動して CLI を実行しないでください。[Vercel の monorepo 手順](https://vercel.com/docs/monorepos)に合わせています。

```powershell
npm.cmd ci
npx.cmd --yes vercel@60.1.3 login
npx.cmd --yes vercel@60.1.3 link
```

`link` で利用するアカウント・チームを選び、既存プロジェクトを選択、または `tsuyulabo` を作成します。コードの場所を聞かれたら `./` を選びます。続いて Vercel Dashboard → 対象 Project → **Settings → Build and Deployment** で次を保存します。

| 項目 | 値 |
| --- | --- |
| Framework Preset | Next.js |
| Root Directory | `apps/web` |
| Include source files outside of the Root Directory | 有効 |
| Node.js Version | 22.x |
| Install Command | `cd ../.. && npm ci`（`vercel.json` で指定済み） |
| Build Command | `npm run build`（`vercel.json` で指定済み） |
| Output Directory | Next.js の既定値 |

ルートの `package-lock.json` と npm workspaces を使ってインストールします。`apps/web/vercel.json` は Git push による自動デプロイも無効にしています。手動 CLI またはこのリポジトリの手動 Actions を使ってください。

**Settings → Environment Variables** で `NEXT_PUBLIC_DEV_TOOLS=0` を Production に設定します。公開デモでは **`NEXT_PUBLIC_API_URL` を作成しません**。既に設定されている場合は Production から削除します。

```powershell
npx.cmd --yes vercel@60.1.3 env add NEXT_PUBLIC_DEV_TOOLS production
# 対話入力: 0
npx.cmd --yes vercel@60.1.3 deploy --prod
```

表示された URL を開くと「公開デモ」のカードが出ます。ごはん・しつけの練習、羽化・研究発表会のデモを確認します。育成の保存や報酬の付与はありません。API を設定した本番とローカル開発では通常のホームを使います。

## 2. Neon と Upstash を作る

### Neon（Postgres）

1. Neon Console → **New Project**。Cloud Run の東京リージョンに近いリージョンを選び、Postgres 16 のデータベース `tsuyulabo` を作成します。
2. **SQL Editor** で対象の branch / database を選び、次を実行します。

   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
   ```

3. **Connect** の **Connection pooling をオフ**にして直接接続用 URL を取得します。今回は小規模なので API・worker・migration とも直接接続を使います。接続数は API 最大 2 台、worker 最大 1 台から実測します。
4. このアプリは SQLAlchemy + asyncpg です。URL の先頭を `postgresql+asyncpg://` にし、クエリは `?ssl=require` にします。Neon が表示する `sslmode=require` と `channel_binding=require` はそのまま渡さず削除してください。パスワードの URL エンコードを保持します。

   ```text
   postgresql+asyncpg://USER:URL_ENCODED_PASSWORD@ep-EXAMPLE.REGION.aws.neon.tech/tsuyulabo?ssl=require
   ```

`vector` は対象データベースごとに必要です。スキーマ作成は後述の migration job が行います。拡張の説明は [Neon pgvector](https://neon.com/docs/extensions/pgvector)、接続方式は [SQLAlchemy asyncpg](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.asyncpg) を参照してください。

### Upstash（Redis）

1. Upstash Console → **Redis → Create Database**。Cloud Run / Neon に近いリージョンを選びます。
2. **Connect** で Redis クライアント用の接続情報を取得します。REST URL / REST TOKEN ではありません。
3. TLS を使う `rediss://default:PASSWORD@HOST:PORT/0` を保存します。パスワード内の特殊文字は URL エンコードします。キューのキーが追い出されないよう eviction は無効にします。
4. **Usage** でコマンド数、容量、接続数を確認します。arq はアイドル中もポーリングするため、無料枠だけで常時稼働できるとは限りません。[互換性](https://upstash.com/docs/redis/help/faq)と[料金](https://upstash.com/pricing/redis)も確認してください。

## 3. Google Cloud の初期設定

Google Cloud Console で専用 Project を作成し、請求先を関連付けます。**Billing → Budgets & alerts** で予算通知を作成します（通知は利用停止の上限ではありません）。以降の初期設定は右上の **Cloud Shell**（Bash）で実行できます。

```bash
export PROJECT_ID='YOUR_PROJECT_ID'
export REGION='asia-northeast1'
gcloud config set project "$PROJECT_ID"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com iam.googleapis.com iamcredentials.googleapis.com sts.googleapis.com
gcloud artifacts repositories create tsuyulabo --repository-format=docker --location="$REGION" --immutable-tags --description='Tsuyu Labo release images'
gcloud iam service-accounts create tsuyulabo-runtime --display-name='Tsuyu Labo runtime'
gcloud iam service-accounts create tsuyulabo-deployer --display-name='Tsuyu Labo GitHub deployer'
```

既存の同名リソースがある場合は作成を繰り返さず、そのリソースを確認して使います。Artifact Registry はタグを変更できない設定です。公開ごとに別のタグを付け、ロールバック先を残します。

### Secret Manager

Console → **Security → Secret Manager → Create Secret** で以下を作成し、値を貼り付けます。末尾改行を含めないでください。最初の有効バージョン番号は `1` です。秘密の値を GitHub やコード、コマンド履歴に保存する必要はありません。

| コンテナ内の名前 | Secret Manager の名前 | 内容 / 使用先 |
| --- | --- | --- |
| `DATABASE_URL` | `tsuyulabo-database-url` | 上記 Neon URL / API・worker・migration |
| `REDIS_URL` | `tsuyulabo-redis-url` | 上記 TLS Redis URL / API・worker |
| `JWT_SECRET` | `tsuyulabo-jwt-secret` | 十分に長いランダム値 / API・worker |
| `OPENAI_API_KEY` | `tsuyulabo-openai-api-key` | 任意。OpenAI 利用時のみ / API・worker |
| `ANTHROPIC_API_KEY` | `tsuyulabo-anthropic-api-key` | 任意。Anthropic 利用時のみ / API・worker |

JWT の値はパスワードマネージャーの生成機能などで 32 バイト以上の乱数から作ります。全 API インスタンスで同じ値を使用します。変更すると既存ゲスト JWT は使えなくなります。

作成後、Cloud Shell で**各 Secret に対して**実行アカウントへ読み取りを付与します。

```bash
for SECRET in tsuyulabo-database-url tsuyulabo-redis-url tsuyulabo-jwt-secret; do
  gcloud secrets add-iam-policy-binding "$SECRET" --member="serviceAccount:tsuyulabo-runtime@$PROJECT_ID.iam.gserviceaccount.com" --role=roles/secretmanager.secretAccessor
done
# LLM を有効にするときは、作った LLM Secret にも同じ binding を追加する。
```

秘密ではない設定はデプロイスクリプトが渡します。

| 環境変数 | 値 |
| --- | --- |
| `CORS_ORIGINS` | 例: `["https://tsuyulabo.vercel.app"]`。JSON 配列、パス・末尾 `/` なし。CLI の `--cors-origin` から生成 |
| `BRAIN_MODE` | `queue` |
| `TSUYU_DEV_TOOLS` | `0`（本番固定） |
| `SHIORI_PROVIDER` | `mock`（既定）、`openai`、`anthropic` |
| `OMP_NUM_THREADS`, `MKL_NUM_THREADS` | `1`（1 CPU 内での過剰なスレッド作成を抑える） |
| `PORT` | Cloud Run が設定。API は 8000、worker は 8080 |

キーを置くだけでは LLM は有効になりません。`--shiori-provider openai` または `anthropic` が必要です。既定の `mock` は LLM への課金なしで動きます。

## 4. イメージをビルドして Cloud Run に公開する

ローカルには Docker Desktop（Linux containers）、Google Cloud CLI、Python 3.12 以上 / uv が必要です。リポジトリのルートから PowerShell で実行します。

```powershell
gcloud auth login
$project = 'YOUR_PROJECT_ID'
$region = 'asia-northeast1'
$webOrigin = 'https://YOUR_PROJECT.vercel.app'
$tag = (git rev-parse --short HEAD) + '-' + (Get-Date -Format 'yyyyMMddHHmmss')

# 最初はコマンド表示だけ。ネットワーク操作やリソース変更をしない。
.\.tools\uv.exe run python infra/cloudrun/release.py build --project $project --region $region --tag $tag
.\.tools\uv.exe run python infra/cloudrun/release.py deploy --project $project --region $region --tag $tag --cors-origin $webOrigin

# 以下は実際に push / deploy する。オーナーが準備完了後に実行する。
.\.tools\uv.exe run python infra/cloudrun/release.py build --project $project --region $region --tag $tag --execute
.\.tools\uv.exe run python infra/cloudrun/release.py deploy --project $project --region $region --tag $tag --cors-origin $webOrigin --execute
```

`uv.exe` が同梱されていない通常の clone ではインストール済みの `uv` に読み替えます。Linux / Cloud Shell では `uv run python ...`、またはこのスクリプト単独なら `python3 ...` でも動きます。Docker のビルドコンテキストは常にリポジトリのルート、対象は `linux/amd64` です。

公開は次の順序です。コマンドが失敗したら後続へ進みません。

1. `services/api/Dockerfile` と `services/worker/Dockerfile` をビルド。worker には `infra/cloudrun/worker.Dockerfile` で HTTP 起動確認を追加。
2. Artifact Registry に `api:TAG` と `worker:TAG` を push。
3. API と同じイメージで `tsuyulabo-migrate` job を設定し、`alembic -c services/api/alembic.ini upgrade head` を実行。1 task、再試行なし、完了を `--wait` で確認。
4. `tsuyulabo-worker` を公開。内部 ingress / IAM 認証あり、最小・最大 1 台、1 CPU / 1 GiB、常時 CPU。
5. `tsuyulabo-api` を公開。HTTPS で公開、最小 0・最大 2 台、1 CPU / 1 GiB、同時リクエスト 8。ゲーム内の認証には JWT を使用。

Vercel の URL は Cloud Run の公開前に決められるため、CORS と API URL の循環はありません。CORS を追加するときは `--cors-origin` を繰り返します。任意の Vercel Preview URL を許可するワイルドカードは使いません。

### worker をサービスにする理由

現在の arq は常時 Redis を監視し、JST 03:30 のメモ生成も同じプロセス内で実行します。Redis のキュー投入だけでは Cloud Run は 0 台から起動しません。このため **最小 1 台 + `--no-cpu-throttling`** を設定します。[常時 CPU の説明](https://docs.cloud.google.com/run/docs/configuring/billing-settings)を参照してください。

HTTP `/healthz` は arq が Redis に接続して startup hook を終えた後に 200 を返します。外部向け API ではなく起動確認専用で、DB / Redis の継続的な疎通監視は API の `/healthz` とジョブ完了の確認で行います。arq 自体をメインスレッドで動かし、SIGTERM 後は最大 8 秒で処理を待ち、接続を閉じます。長いジョブは再試行され得ます。リビジョン切替では一時的に旧・新 worker が重なるため、厳密な singleton / exactly-once を保証する設定ではありません。

Cloud Run Job + Scheduler なら実行時間だけの課金にできますが、今の無限待機 worker をそのまま job にすると終了しません。burst 実行への変更、投入時の job 起動、定期処理の分離が必要で、しつけの短い応答待ちや即時質問との相性も変わります。このリリースは既存のキュー動作を維持する常駐サービスを選びます。

## 5. Web と API をつなぐ

```powershell
$apiUrl = gcloud run services describe tsuyulabo-api --project $project --region $region --format='value(status.url)'
Write-Output $apiUrl
npx.cmd --yes vercel@60.1.3 env add NEXT_PUBLIC_API_URL production
# 対話入力: 上に表示された https://...run.app （末尾 /v1 は付けない）
npx.cmd --yes vercel@60.1.3 deploy --prod
```

既存値を変更する場合は Dashboard → Environment Variables で編集します。`NEXT_PUBLIC_API_URL` は公開されるビルド時の値です。変更後は必ず再ビルド・再公開します。DB URL や JWT / LLM キーに `NEXT_PUBLIC_` を付けないでください。

## 6. GitHub Actions を有効にする（WIF、初回のみ）

`.github/workflows/deploy.yml` は **workflow_dispatch のみ**です。設定が不足している対象は通知と Summary に不足名を出してスキップし、ログイン・ビルド・公開を開始しません。データベースの秘密値は Google Secret Manager に置き、GitHub には WIF の識別子と Vercel token だけを設定します。

### Google と GitHub の信頼関係

Cloud Shell の Bash で、前述の `$PROJECT_ID` を設定したまま実行します。GitHub の owner / repository **数値 ID** は `https://api.github.com/repos/OWNER/REPO` の `owner.id` と `id` で確認できます。文字列名の再利用による誤許可を避けるため数値 ID で制限します。

```bash
export REPOSITORY_ID='GITHUB_REPOSITORY_NUMERIC_ID'
export OWNER_ID='GITHUB_OWNER_NUMERIC_ID'
export PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
export DEPLOYER="tsuyulabo-deployer@$PROJECT_ID.iam.gserviceaccount.com"
export RUNTIME="tsuyulabo-runtime@$PROJECT_ID.iam.gserviceaccount.com"

gcloud iam workload-identity-pools create github --location=global --display-name='GitHub Actions'
gcloud iam workload-identity-pools providers create-oidc github --location=global --workload-identity-pool=github --issuer-uri=https://token.actions.githubusercontent.com --attribute-mapping='google.subject=assertion.sub,attribute.repository_id=assertion.repository_id' --attribute-condition="assertion.repository_owner_id=='$OWNER_ID' && assertion.repository_id=='$REPOSITORY_ID' && assertion.ref=='refs/heads/main' && assertion.event_name=='workflow_dispatch'"
gcloud iam service-accounts add-iam-policy-binding "$DEPLOYER" --role=roles/iam.workloadIdentityUser --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository_id/$REPOSITORY_ID"

gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$DEPLOYER" --role=roles/run.admin
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$DEPLOYER" --role=roles/serviceusage.serviceUsageConsumer
gcloud artifacts repositories add-iam-policy-binding tsuyulabo --location="$REGION" --member="serviceAccount:$DEPLOYER" --role=roles/artifactregistry.writer
gcloud iam service-accounts add-iam-policy-binding "$RUNTIME" --member="serviceAccount:$DEPLOYER" --role=roles/iam.serviceAccountUser

gcloud iam workload-identity-pools providers describe github --location=global --workload-identity-pool=github --format='value(name)'
echo "$DEPLOYER"
```

最後の 2 つの出力を以下の Secrets に登録します。デプロイヤーに Secret の値の閲覧権限は付けません。実行アカウントが起動時に読みます。初期設定を実行するオーナーには IAM / Service Usage / Secret 管理の権限が必要です。[Google の WIF 手順](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines)と [auth Action](https://github.com/google-github-actions/auth) を参照してください。

### GitHub に設定するもの

Repository → **Settings → Secrets and variables → Actions** で登録します。

| 種類 | 名前 | 値 |
| --- | --- | --- |
| Secret | `GCP_WIF_PROVIDER` | `projects/数字/locations/global/workloadIdentityPools/github/providers/github` |
| Secret | `GCP_DEPLOY_SERVICE_ACCOUNT` | `tsuyulabo-deployer@PROJECT_ID.iam.gserviceaccount.com` |
| Secret | `VERCEL_TOKEN` | Vercel Account Settings → Tokens で作成（対象チームへのアクセスを付与） |
| Variable | `GCP_PROJECT_ID` | Google Cloud Project ID |
| Variable | `GCP_REGION` | `asia-northeast1`（省略時も同じ） |
| Variable | `WEB_ORIGIN` | 本番 Web の origin、例 `https://tsuyulabo.vercel.app` |
| Variable | `GCP_SECRET_VERSION` | `1`（既定）。利用する全 Secret に存在する有効な番号 |
| Variable | `SHIORI_PROVIDER` | `mock`（既定）、`openai`、`anthropic` |
| Variable | `VERCEL_ORG_ID` | `vercel link` がルートの `.vercel/project.json` に保存する `orgId` |
| Variable | `VERCEL_PROJECT_ID` | 同ファイルの `projectId` |

サービスアカウントの JSON 鍵は作成不要です。Secret Manager の version は `latest` を使わず番号を固定します。ローテーション時は利用する全 Secret のバージョン番号をそろえて変数を更新し、再デプロイします。

workflow を main に取り込んだ後、**Actions → deploy → Run workflow → Branch: main** で `web` / `backend` / `all` を選びます。WIF は main の手動実行だけを許可します。初回は `web`（デモ）、`backend`、Vercel の API URL 設定、`web` の順です。2 回目以降の `all` は backend 成功後に Web を公開します。backend 設定自体がない場合は `all` でも Web だけ公開できます。Vercel は Production の環境変数を使ってリモートビルドします。

## 7. 公開後の確認

```powershell
Invoke-RestMethod "$apiUrl/healthz"
Invoke-RestMethod "$apiUrl/v1/clock"
gcloud run services logs read tsuyulabo-worker --project $project --region $region --limit 30
gcloud run jobs executions list --job tsuyulabo-migrate --project $project --region $region
```

API の health に DB と Redis の成功が出ること、migration の成功、worker の起動を確認します。Web で卵を受け取り、シオリへの質問や実験が完了することも確認します。API の health だけでは worker のジョブ処理まで保証しません。CORS の問題はブラウザーの Network で `Origin` と `CORS_ORIGINS` を照合してください。

### 既存 smoke_api.py で一週間を確認する

`scripts/smoke_api.py` はゲスト・育成データを作り、開発用の時間操作を呼びます。**`TSUYU_DEV_TOOLS=0` の本番では完走しません**。本番を変更せず、別の Google Cloud project、Neon branch / DB、Upstash database を使う検証環境で第 2〜4 節を実施します。検証用 API だけで一時的に時間操作を有効にします。

```powershell
$stagingProject = 'YOUR_STAGING_PROJECT_ID'
gcloud run services update tsuyulabo-api --project $stagingProject --region $region --update-env-vars TSUYU_DEV_TOOLS=1
$stagingApiUrl = gcloud run services describe tsuyulabo-api --project $stagingProject --region $region --format='value(status.url)'
.\.tools\uv.exe run python scripts/smoke_api.py --base $stagingApiUrl
# 上記は scripts/smoke_api.py --base https://...run.app に相当する。
gcloud run services update tsuyulabo-api --project $stagingProject --region $region --update-env-vars TSUYU_DEV_TOOLS=0
```

成功時はゲスト作成、育成、パズル、しつけ、キュー経由のシオリ応答が表示されます。失敗しても最後の無効化を実行してください。検証後はオーナーが検証用 Cloud Run サービスを削除するなどして課金を止めます。

## 8. 費用と停止・更新

企画書 §14 の**目標**は次のとおりです。実測で見直す目安であり、各社の固定料金ではありません。

| 段階 | 規模 / 構成 | 月額目安 |
| --- | --- | --- |
| ポートフォリオ版 | 〜100 人、Vercel、Cloud Run API + worker、小さい Neon Postgres、Upstash | **0〜3,000 円 + LLM** |
| β版 | 〜3,000 人、常時 1 台、Cloud SQL、Redis、Scheduler 等 | 1〜3 万円 + LLM |

今回の常駐 worker を 24 時間動かす設定は、ポートフォリオ版の目標額を保証しません。[Cloud Run 料金](https://cloud.google.com/run/pricing)の米国 Tier 1 単価を比較用に使うと、1 CPU + 1 GiB × 30 日は無料枠控除後で約 **47 USD / 月**（仮に 1 USD = 150 円なら約 7,000 円）です。東京の料金、為替、API・転送・ログ等は別途確認します。

| 項目 | 小規模での考え方 |
| --- | --- |
| Vercel | Hobby の利用条件・無料枠内で公開デモを先行可能 |
| Cloud Run API / migration | 最小 0 台 / 実行時のみ。リクエスト・CPU・転送次第 |
| Cloud Run worker | 常時 1 台の固定的な費用。最小 0 への変更だけではキューが起動しない |
| Neon | Free 枠を検討。計算時間・容量・復元期間を Console で確認 |
| Upstash | worker の 1 秒ポーリングは月約 259 万回、複数 Redis コマンドを伴うため無料枠を超え得る |
| Artifact Registry / Secret Manager / Logging | イメージ保持量、Secret 利用、ログ量に応じる。古いイメージの整理を設定 |
| LLM | `mock` は 0。実プロバイダーは利用量に別途課金 |

0〜3,000 円を優先する間は Web の公開デモのみ、または期間を決めたバックエンド検証にします。常時サービスの費用を削減する Job 化は前述のアプリ側変更が必要です。[Vercel 料金](https://vercel.com/pricing)、[Neon 料金](https://neon.com/pricing)、[Upstash 料金](https://upstash.com/pricing/redis)で契約時点の条件を確認してください。

更新前は Neon のバックアップ / branch による復元手段を確認します。migration は旧 API・worker がまだ動いている状態で走るので、互換性のある追加変更を原則とします。失敗時は Cloud Run Jobs のログを確認し、修正後に新しいタグで実行します。API のリビジョンを戻しても DB は自動で戻りません。

公開を止める場合は、先に Web の API URL を削除して再公開し、デモへ切り替えます。その後 Cloud Run Console で API と worker を削除すれば常駐課金が止まります。DB・Redis・Artifact Registry の保持課金は別なので、残すデータを確認して管理します。次回は同じ release script でサービスを再作成できます。

## 9. ローカル検証

```powershell
.\.tools\uv.exe run ruff check infra/cloudrun
.\.tools\uv.exe run ruff format --check infra/cloudrun
.\.tools\uv.exe run pytest infra/cloudrun
npm.cmd run lint -w apps/web
npm.cmd run test -w apps/web
$env:NODE_ENV = 'production'
$env:NEXT_PUBLIC_DEV_TOOLS = '0'
$env:NEXT_PUBLIC_API_URL = ''
npm.cmd run build -w apps/web
$env:NEXT_PUBLIC_API_URL = 'https://api.example.com'
npm.cmd run build -w apps/web
# actionlint があれば:
actionlint .github/workflows/deploy.yml
# Docker に接続できれば（push / deploy はしない）:
docker build --platform=linux/amd64 -f services/api/Dockerfile -t tsuyulabo-api:validation .
docker build --platform=linux/amd64 -f services/worker/Dockerfile -t tsuyulabo-worker-base:local .
docker build --platform=linux/amd64 -f infra/cloudrun/worker.Dockerfile -t tsuyulabo-worker:validation .
```
