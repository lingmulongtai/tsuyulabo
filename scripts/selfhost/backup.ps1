# Dump the self-hosted database to a timestamped file and keep the newest few (docs/selfhost.md).
#
#   powershell -ExecutionPolicy Bypass -File scripts/selfhost/backup.ps1 [-BackupDir <dir>] [-Keep 14] `
#       [-MirrorDirs F:\tsuyulabo-backups] [-MirrorKeep 30]
#
# pg_dump writes inside the container and `docker cp` copies the file out, because PowerShell
# redirection would re-encode the binary dump as text. Mirrors on another disk survive a C: failure;
# a mirror that is unavailable is reported but does not lose the primary backup.
param(
    [string]$BackupDir = (Join-Path $HOME "tsuyulabo-backups"),
    [int]$Keep = 14,
    [string[]]$MirrorDirs = @(),
    [int]$MirrorKeep = 30,
    [string]$Project = "tsuyulabo-server",
    [string]$EnvFile = (Join-Path $HOME ".tsuyulabo\selfhost.env")
)
$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Exe $($Arguments -join ' ') failed with exit code $LASTEXITCODE" }
}

function Remove-OldDumps {
    param([string]$Directory, [int]$Count)
    Get-ChildItem $Directory -Filter "tsuyulabo-*.dump" | Sort-Object Name -Descending |
        Select-Object -Skip $Count | Remove-Item -Force
}

# Scheduled tasks may start before Docker Desktop's per-user CLI is on PATH.
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    $env:Path = (Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\resources\bin") + ";" + $env:Path
}

$settings = @{}
foreach ($line in Get-Content $EnvFile) {
    if ($line -match '^(POSTGRES_USER|POSTGRES_DB)=(.+)$') { $settings[$Matches[1]] = $Matches[2] }
}
$container = (docker ps --filter "label=com.docker.compose.project=$Project" `
    --filter "label=com.docker.compose.service=postgres" --format "{{.Names}}" | Select-Object -First 1)
if (-not $container) { throw "postgres container for project $Project is not running" }

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$target = Join-Path $BackupDir "tsuyulabo-$stamp.dump"
Invoke-Checked docker @(
    "exec", $container, "pg_dump", "-U", $settings["POSTGRES_USER"], "-d", $settings["POSTGRES_DB"],
    "-Fc", "-f", "/tmp/tsuyulabo-backup.dump"
)
Invoke-Checked docker @("cp", "${container}:/tmp/tsuyulabo-backup.dump", $target)
Invoke-Checked docker @("exec", $container, "rm", "-f", "/tmp/tsuyulabo-backup.dump")
Write-Output "backup written: $target ($((Get-Item $target).Length) bytes)"
Remove-OldDumps $BackupDir $Keep

$mirrorFailed = $false
# `powershell -File` passes "A,B" as one string, so accept comma-separated lists too.
$mirrors = $MirrorDirs | ForEach-Object { $_ -split "," } | ForEach-Object { $_.Trim().Trim('"') } |
    Where-Object { $_ }
foreach ($mirror in $mirrors) {
    # A sleeping USB disk can fail the first access, so retry a few times before giving up.
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            New-Item -ItemType Directory -Force -Path $mirror | Out-Null
            Copy-Item $target -Destination $mirror -Force
            Remove-OldDumps $mirror $MirrorKeep
            Write-Output "mirrored to: $mirror"
            break
        } catch {
            if ($attempt -lt 3) { Start-Sleep -Seconds 10; continue }
            $mirrorFailed = $true
            Write-Warning "mirror $mirror failed: $($_.Exception.Message)"
        }
    }
}
if ($mirrorFailed) { exit 2 }
