# GitCheck 1-Line Installer for Windows (PowerShell)
# Usage:
#   irm https://raw.githubusercontent.com/SumitJambhale/GitCheck/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

$repo = "SumitJambhale/GitCheck"
$binName = "git-check.exe"
$assetName = "git-check-windows-amd64.exe"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "          Installing GitCheck CLI (Windows)       " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Determine version
$tag = $env:GITCHECK_VERSION
if (-not $tag) {
    Write-Host "Checking latest release on GitHub..."
    try {
        $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/releases/latest"
        $tag = $release.tag_name
    } catch {
        $tag = "v0.1.0"
        Write-Host "Falling back to release tag $tag" -ForegroundColor Yellow
    }
}

Write-Host "Installing version: $tag" -ForegroundColor Green

# 2. Destination directory
$installDir = "$HOME\.git-check\bin"
if (-not (Test-Path -Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

$destPath = Join-Path -Path $installDir -ChildPath $binName
$downloadUrl = "https://github.com/$repo/releases/download/$tag/$assetName"

Write-Host "Downloading from: $downloadUrl..."
Invoke-WebRequest -Uri $downloadUrl -OutFile $destPath -UseBasicParsing

# 3. Add to user PATH if not present
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$installDir*") {
    Write-Host "Adding $installDir to User PATH..." -ForegroundColor Cyan
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$installDir", "User")
    $env:PATH = "$env:PATH;$installDir"
}

Write-Host "`nGitCheck CLI installed successfully!" -ForegroundColor Green
Write-Host "Quick Start:"
Write-Host "  1. Set your LLM key: `$env:GEMINI_API_KEY=`"your-key`""
Write-Host "  2. Go to your repo: cd path\to\repo"
Write-Host "  3. Install git hook: git-check install-hook"
