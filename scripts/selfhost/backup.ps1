# Dump the self-hosted database to a timestamped file and keep the newest few (docs/selfhost.md).
#
#   powershell -ExecutionPolicy Bypass -File scripts/selfhost/backup.ps1 [-BackupDir <dir>] [-Keep 14]
#
# pg_dump writes inside the container and `docker cp` copies the file out, because PowerShell
# redirection would re-encode the binary dump as text.
param(
    [string]$BackupDir = (Join-Path $HOME "tsuyulabo-backups"),
    [int]$Keep = 14,
    [string]$Project = "tsuyulabo-server",
    [string]$EnvFile = (Join-Path $HOME ".tsuyulabo\selfhost.env")
)
$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Exe $($Arguments -join ' ') failed with exit code $LASTEXITCODE" }
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

Get-ChildItem $BackupDir -Filter "tsuyulabo-*.dump" | Sort-Object Name -Descending |
    Select-Object -Skip $Keep | Remove-Item -Force
