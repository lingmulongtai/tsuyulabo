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
