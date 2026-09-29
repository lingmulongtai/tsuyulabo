# Deploy a git ref to the self-hosted server on this PC (docs/selfhost.md).
#
#   powershell -ExecutionPolicy Bypass -File scripts/selfhost/deploy.ps1 [-Ref origin/main]
#
# The server runs from its own clone outside OneDrive, so work in progress never reaches players.
# It uses its own compose project name, so its containers and volumes never mix with `docker compose up` in dev.
param(
    [string]$Ref = "origin/main",
    [string]$ServerDir = (Join-Path $HOME "srv\tsuyulabo"),
    [string]$EnvFile = (Join-Path $HOME ".tsuyulabo\selfhost.env"),
    [string]$Project = "tsuyulabo-server",
    [int]$HealthTimeoutSeconds = 300
)
$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Exe $($Arguments -join ' ') failed with exit code $LASTEXITCODE" }
}

if (-not (Test-Path $EnvFile)) {
    throw "missing $EnvFile; create it once with: uv run python scripts/selfhost/init_env.py"
}
if (-not (Test-Path (Join-Path $ServerDir ".git"))) {
    Invoke-Checked git @("clone", "-q", "https://github.com/lingmulongtai/tsuyulabo.git", $ServerDir)
}
Invoke-Checked git @("-C", $ServerDir, "fetch", "-q", "origin")
Invoke-Checked git @("-C", $ServerDir, "checkout", "-q", "--detach", $Ref)
$commit = (git -C $ServerDir log -1 --format="%h %s")
Write-Output "deploying $commit"

$compose = @(
    "compose", "--project-name", $Project, "--project-directory", $ServerDir, "--env-file", $EnvFile,
    "-f", (Join-Path $ServerDir "docker-compose.yml"), "-f", (Join-Path $ServerDir "docker-compose.selfhost.yml")
)
Invoke-Checked docker ($compose + @("up", "-d", "--build", "--remove-orphans"))

$deadline = (Get-Date).AddSeconds($HealthTimeoutSeconds)
while ($true) {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/healthz" -TimeoutSec 5
        Write-Output "api healthy: $($health | ConvertTo-Json -Compress)"
        break
    } catch {
        if ((Get-Date) -gt $deadline) { throw "api did not become healthy within $HealthTimeoutSeconds s" }
        Start-Sleep -Seconds 5
    }
}
Invoke-Checked docker ($compose + @("ps"))
Write-Output "deployed $commit"
