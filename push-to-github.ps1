# Create a GitHub repo from this project and push master.
# Usage: ./push-to-github.ps1 [repo-name] [public|private]
# Defaults: name = tg-secretary, visibility = private.

$ErrorActionPreference = "Stop"
$repoName = if ($args[0]) { $args[0] } else { "tg-secretary" }
$visibility = if ($args[1] -eq "public") { "--public" } else { "--private" }

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "Installing GitHub CLI via winget..."
    winget install --id GitHub.cli -e --accept-package-agreements --accept-source-agreements --silent
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + `
                [Environment]::GetEnvironmentVariable("Path", "Machine")
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        throw "gh install failed. Install manually from https://cli.github.com/ then re-run."
    }
}

gh auth status 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Authenticating with GitHub (a browser tab will open)..."
    gh auth login --hostname github.com --git-protocol https --web
}

gh repo create $repoName $visibility --source . --remote origin --push `
    --description "Telegram Business secretary bot: Gemini AI auto-replies, quiet hours, per-chat context, SOCKS5 proxy"

Write-Host ""
Write-Host "Repo URL:" -NoNewline
Write-Host " " -NoNewline
gh repo view --json url --jq .url
