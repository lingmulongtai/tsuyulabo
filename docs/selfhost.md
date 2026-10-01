# オーナーの PC でサーバーを動かす（自宅サーバー）

2026-09-29 から、ゲームの API は Cloud Run ではなく**オーナーの PC**（ROG Zephyrus G14、Tailscale 名 `ozg14`）で動かす。
Web は今までどおり Vercel、API だけをこの PC から **Tailscale Funnel** で公開する。Cloud Run の手順（[deploy.md](deploy.md)）は、
将来クラウドに移すときのために残しておく。

```
スマホ・ブラウザ ──https──> tsuyulabo.vercel.app（Web、Vercel）
                                │ /v1/* と /healthz を転送
                                └──https──> ozg14.tail4204cd.ts.net（Tailscale Funnel）
                                                 └──> 127.0.0.1:8000（この PC の Docker: api / worker / postgres / redis）
```

## 1. 最初に 1 回だけ

1. **WSL2 と Docker Desktop** を入れる（管理者の PowerShell。途中で再起動）。この PC では Docker Desktop はユーザー単位で
   入っていて、CLI は `%LOCALAPPDATA%\Programs\DockerDesktop
esourcesin` にある。

   ```powershell
   wsl --install --no-distribution
   winget install -e --id Docker.DockerDesktop
   ```

   Docker Desktop の設定で「Start Docker Desktop when you sign in」を ON にする。
2. **電源**: 電源接続時はスリープしない。フタを閉じても動かすなら「カバーを閉じたときの動作」を電源接続時「何もしない」にする。
3. **秘密の値**を作る（DB のパスワード、JWT の鍵、Web Push の鍵）。保存先は `~/.tsuyulabo/selfhost.env`。
   **リポジトリにも OneDrive にも置かない**（OneDrive は学校のアカウントなので）。すでにあるときは上書きしない。

   ```bash
   uv run python scripts/selfhost/init_env.py
   ```

   このファイルがなくなると、DB に入れなくなり、全員のログインが切れる。別の場所（パスワードマネージャーなど）にも控えておく。
4. **Tailscale Funnel** で API を公開する。初回はコマンドが出す URL を開いて、管理画面で HTTPS と Funnel を許可する。

   ```powershell
   tailscale funnel --bg 8000
   tailscale funnel status
   ```

   `--bg` で設定は保存され、再起動しても続く。止めるときは `tailscale funnel --https=443 off`。

## 2. デプロイ（main を本番に出す）

```powershell
powershell -ExecutionPolicy Bypass -File scripts/selfhost/deploy.ps1
```

- 本番は開発フォルダ（OneDrive）ではなく、専用の clone `C:\Users\lingm\srv\tsuyulabo` で動く。スクリプトが `origin/main` を
  取ってきて、`docker compose` でビルドと起動をし、`/healthz` が通るまで待つ。**push していない変更は本番に出ない。**
- 特定のコミットに戻すときは `-Ref <コミット>`。
- Docker のプロジェクト名は `tsuyulabo-server`。開発用の `docker compose up`（プロジェクト名 `tsuyulabo`）とは
  コンテナも DB も別になる。
- 設定は [docker-compose.selfhost.yml](../docker-compose.selfhost.yml)。本番の設定（`TSUYU_ENV=production`、時間スキップなし、
  再起動で自動復帰、Web の dev サーバーは起動しない）を `docker-compose.yml` に重ねている。

## 3. Web と API をつなぐ（Vercel）

ブラウザは API を**直接呼ばない**。Web と同じ `https://tsuyulabo.vercel.app/v1/...` に送り、Vercel が自宅サーバーへ転送する
（[proxy.ts](../apps/web/src/lib/api/proxy.ts)）。直接呼ぶと、Tailscale につないだ端末では `ozg14.tail4204cd.ts.net` が
プライベートな 100.x のアドレスになり、Chrome の Local Network Access に止められるため（2026-10-01 に確認）。

Vercel の Production の環境変数（ビルドのときに使う値なので、変えたら必ず再公開する）:

| 変数 | 値 | 意味 |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `https://tsuyulabo.vercel.app` | ブラウザが API を呼ぶ先（Web 自身） |
| `TSUYU_API_PROXY_TARGET` | `https://ozg14.tail4204cd.ts.net` | Vercel が転送する先（ブラウザには出ない） |
| `NEXT_PUBLIC_DEV_TOOLS` | `0` | 時間スキップなどを出さない |

```powershell
npx.cmd --yes vercel@60.1.3 env ls production
npx.cmd --yes vercel@60.1.3 deploy --prod --yes
```

API 側の `CORS_ORIGINS` は `https://tsuyulabo.vercel.app` だけを許可している（転送されたリクエストにも Origin が付くため）。
Android アプリも Vercel の URL を読み込むので、同じ経路を通る。

## 4. バックアップ

**毎朝 5:00 に自動で取っている**（タスク スケジューラ「tsuyulabo-backup」、2026-10-01 登録。PC が止まっていて逃したら、
次に起動したときに実行）。保存先:

| 場所 | 残す数 | 意味 |
| --- | --- | --- |
| `C:\Users\lingm\tsuyulabo-backups\` | 14 | ふだん戻す用。`backup.log` に毎回の結果 |
| `F:\tsuyulabo-backups\`（USB の外付け SSD） | 30 | C ドライブが壊れても残る。外れていたら警告だけ出して続ける |

学校の OneDrive には置かない（遊んでいる人のデータなので）。手で取るとき:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/selfhost/backup.ps1 -MirrorDirs "F:\tsuyulabo-backups"
```

タスクは本番用 clone（`C:\Users\lingm\srv\tsuyulabo`）のスクリプトを動かす。登録し直すとき:

```powershell
$script = "$HOME\srv\tsuyulabo\scripts\selfhost\backup.ps1"; $log = "$HOME\tsuyulabo-backups\backup.log"
$arg = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command `"& '$script' -MirrorDirs 'F:\tsuyulabo-backups' *>> '$log'`""
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "tsuyulabo-backup" -Action (New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg) -Trigger (New-ScheduledTaskTrigger -Daily -At 5:00) -Settings $settings
```

戻すとき（中身を全部置き換える。先に今の状態もバックアップする）:

```powershell
docker cp <dumpファイル> tsuyulabo-server-postgres-1:/tmp/restore.dump
docker exec tsuyulabo-server-postgres-1 pg_restore -U tsuyu -d tsuyulabo --clean --if-exists /tmp/restore.dump
```

## 5. 確認とログ

```powershell
Invoke-RestMethod https://ozg14.tail4204cd.ts.net/healthz
docker compose --project-name tsuyulabo-server logs --tail 50 api worker
```

## 6. 気をつけること

- **PC が止まるとゲームも止まる**: スリープ、シャットダウン、Windows Update の再起動のあいだは遊べない。再起動のあとは
  Windows にサインインすると Docker Desktop が立ち上がり、コンテナも自動で戻る（`restart: unless-stopped`）。
- **CPU は冷えにくい**（液体金属の劣化）。api と worker は 2 コアずつ、PyTorch は 2 スレッドに絞っている。
  変えるときは env ファイルに `SELFHOST_API_CPUS` / `SELFHOST_WORKER_CPUS` / `SELFHOST_TORCH_THREADS` を書く。
- 公開しているのは API（ポート 8000）だけ。Postgres と Redis は `127.0.0.1` にしか出していない。
- 開発用の時間スキップは本番では無効（`TSUYU_DEV_TOOLS=0`）。`scripts/smoke_api.py` は本番では最後まで通らないので、
  開発用の `docker compose up` で試す。

## 7. レート制限とジョブ受付

Redis の原子的固定窓カウンターで全 API プロセスの回数を共有する。分・時間・日はサーバー実時刻の窓（UTC、日次は 0 時）で、ゲーム時計とは別。窓境界のバーストはありうる。

| 環境変数 | 既定値 | 対象 |
| --- | --- | --- |
| `RATE_LIMITS_ENABLED` | `true` | Redis レート制限（ジョブ受付上限とは独立） |
| `TRUSTED_PROXY_HOPS` | `1` | X-Forwarded-For の右から選ぶ位置。`0` は socket peer のみ |
| `RATE_GUEST_HOUR` | `5` | ゲスト作成 / IP / 時間 |
| `RATE_GUEST_DAY_GLOBAL` | `200` | ゲスト作成 / 全体 / 日 |
| `RATE_GUEST_FALLBACK_HOUR_GLOBAL` | `10` | Redis 障害中のゲスト / API プロセス全体 / 時間 |
| `RATE_SHIORI_MINUTE` / `RATE_SHIORI_DAY` | `10` / `100` | シオリ POST / ユーザー / 分・日 |
| `RATE_BRAIN_MINUTE` | `20` | 個体の experiments・behavior・brain/activity、GET 含む / ユーザー / 分 |
| `RATE_PUZZLE_MINUTE` | `60` | puzzles・daily-circuit / ユーザー / 分 |
| `RATE_FRIENDS_MINUTE` | `30` | friends（一覧・解除も含む）/ ユーザー / 分 |
| `RATE_AUTHENTICATED_MINUTE` | `300` | 認証済み全操作の合計 / ユーザー / 分。専用制限と両方適用 |
| `JOB_MAX_PER_USER` / `JOB_MAX_TOTAL` | `2` / `20` | pending + running のジョブ、ユーザー / 全体 |
| `JOB_BUSY_RETRY_AFTER` | `10` | 503 の再試行待ち秒数（受付枠の予約ではない） |
| `WORKER_MAX_JOBS` | `2` | worker 1 プロセス内の並行数。既存のタイムアウト 180 秒は維持 |

値を変更するときは `~/.tsuyulabo/selfhost.env` に書き、通常のデプロイスクリプトでコンテナを再作成する。Compose はこれらの値を API / worker に渡す。各回数・ジョブ数は 1 以上、hops は 0〜16。
worker を増やすと並行数も増えるため、2 CPU のホストでは worker 1 台・`WORKER_MAX_JOBS=2` を維持する。

429 `rate_limited` と 503 `server_busy` は既存のエラー形式で `details.retry_after` と `Retry-After` を返す。Web は自動再試行を止め、同じパスへの再送を待ち時間まで通信せず、日本語の案内を表示する。
Redis に接続できないと、通常の育成・読み取りは fail open。ログは最長 1 分ごとに警告し、ゲストのみ小さな全体メモリ上限を使う。これは IP を増やしても回避できないが、API 再起動でリセットされ、複数プロセス間では共有されない。DB のジョブ上限は Redis 障害中も有効。

### Funnel と接続元 IP

2026-10-01 に確認した [Tailscale 上流の `addProxyForwardedHeaders`](https://github.com/tailscale/tailscale/blob/main/ipn/ipnlocal/serve.go) は、`X-Forwarded-For` を `SrcAddr` の IP で**上書き**する（append ではない）。
そのためこの構成の既定値は `TRUSTED_PROXY_HOPS=1`。Docker gateway の socket peer ではなく、Funnel が渡す接続元を使う。
Vercel → Funnel では通常 Vercel の送信元 IP が見え、元のブラウザ IP は保持されない。複数プレイヤーがゲストの IP 上限を共有しうるため、実運用で 429 を確認し、必要なら全体上限を維持したまま IP 上限を調整する。
単に `2` にしても元の IP は復元できず、要素不足で socket peer にフォールバックする。将来 XFF を追記するプロキシを使う場合だけ、`client, proxy` のチェーンを確認して `2` にする。
不正な IP、空要素、長すぎるヘッダー、hops より短いチェーンは socket peer へ戻す。アプリは Uvicorn 等が書き換えた peer を復元できないので、`--forwarded-allow-ips=*` を設定しない。

この調査は上流ソースによるもので、ホストにインストール済みの Tailscale と Vercel の実ヘッダーは未確認。稼働版が違う場合は挙動が変わりうる。
本番経路・直接 Funnel の両方で、認証不要の `/healthz` リクエストを使って **API に届いた** XFF の要素数・位置を一時的に確認する（トークンや個人の IP を永続ログに残さない）。本番にヘッダー表示エンドポイントは追加しない。
Funnel URL は直接呼べるため、異なる IP からのアクセス（append 型チェーンを信頼する構成ではヘッダー偽装も含む）は per-IP 制限を回避しうる。
Redis の全体日次ゲスト上限と DB の全体ジョブ上限はそれでは回避できない。ブラウザ Origin/CORS はスクリプトの防御にはならない。

### 未配信・中断ジョブの回復

受付枠は DB のジョブ行と同じトランザクションで予約する。完了・失敗で解放し、受付拒否では行もゲーム変更も残さない。
ただし DB commit 後・Redis enqueue 前の API 停止、worker のタイムアウト・中断で pending/running が残ると、その行は引き続き枠を消費する。経過時間だけで解放すると、まだキューにある重いジョブを過剰受付するため、自動失効はしない。
503 が続く場合は API / worker のログと、DB の pending/running 件数（ユーザー別・全体）、Redis の待ちジョブ、arq の実行中・再試行状態を照合する。
回復操作は API / worker を停止してバックアップを取り、対象の Redis ジョブが実行・再試行されないことを確認してから、特定した孤立ジョブ ID のみを failed（error と finished_at も設定）へ更新する。正常な待機ジョブを一括削除・失敗扱いにしない。
transactional outbox と孤立ジョブの自動照合は残課題。

Lua と TTL の追加検証（通常の単体テストは Redis 不要）:

```powershell
.\.tools\uv.exe run --with 'fakeredis[lua]' pytest services/api/tests/test_ratelimit_redis.py
```
