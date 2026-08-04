<#
.SYNOPSIS
    Build pipeline: PyInstaller (onedir) -> Inno Setup installer.
    No staging folder: setup.iss packages directly from dist\SORTIS + config.
.PARAMETER SkipBuild
    Skip PyInstaller build, use existing dist\SORTIS\.
#>

param(
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

# ── Paths ─────────────────────────────────────────────────────────────────
$ProjectRoot    = Resolve-Path "$PSScriptRoot\.."
$DistDir        = Join-Path $ProjectRoot "dist"
$BuildDir       = Join-Path $ProjectRoot "build"
$SpecFile       = Join-Path $ProjectRoot "build.spec"
$ReleaseDir     = Join-Path $ProjectRoot "release"
$SetupIss       = Join-Path $PSScriptRoot "setup.iss"

$AppName        = "SORTIS"
$AppVersion     = "2.0.1"
$ExeName        = "SORTIS.exe"
$InstallerName  = "${AppName}_Setup_v${AppVersion}.exe"

# ── Pre-flight ───────────────────────────────────────────────────────────
Write-Host "=== SORTIS Build Pipeline ===" -ForegroundColor Cyan
Write-Host "Project root : $ProjectRoot"
Write-Host ""

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is not on PATH."
}

# ── Phase 1: PyInstaller ─────────────────────────────────────────────────
if (-not $SkipBuild) {
    Write-Host "=== Phase 1: Build EXE ===" -ForegroundColor Green

    if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
    $distSub = Join-Path $DistDir "SORTIS"
    if (Test-Path $distSub) { Remove-Item -Recurse -Force $distSub }

    Write-Host "  -> Running PyInstaller via $SpecFile ..."
    $proc = Start-Process -FilePath "python" -ArgumentList @("-m", "PyInstaller", $SpecFile, "--clean") -NoNewWindow -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        throw "PyInstaller failed with exit code $($proc.ExitCode)."
    }

    $exePath = Join-Path $distSub $ExeName
    if (-not (Test-Path $exePath)) {
        throw "PyInstaller completed but $exePath was not found."
    }
    Write-Host "  -> EXE built: $exePath" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "=== Phase 1: SKIPPED (--SkipBuild) ===" -ForegroundColor Gray
}

# ── Phase 2: Package (Inno Setup) ────────────────────────────────────────
Write-Host "=== Phase 2: Package ===" -ForegroundColor Green

$isccPaths = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
    "${env:ProgramFiles(x86)}\Inno Setup 5\ISCC.exe"
    "${env:ProgramFiles}\Inno Setup 5\ISCC.exe"
    "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
)
$iscc = $null
foreach ($p in $isccPaths) {
    if (Test-Path $p) { $iscc = $p; break }
}
if (-not $iscc) {
    throw "Inno Setup compiler (ISCC.exe) not found. Install from https://jrsoftware.org/isdl.php"
}

$prevInstaller = Join-Path $ReleaseDir $InstallerName
if (Test-Path $prevInstaller) { Remove-Item -Force $prevInstaller }

Write-Host "  -> Compiling installer via Inno Setup..."
& $iscc $SetupIss /Q
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup compilation failed with exit code $LASTEXITCODE."
}

if (-not (Test-Path $prevInstaller)) {
    throw "Installer not found at $prevInstaller"
}
Write-Host "  -> Installer created: $prevInstaller" -ForegroundColor Yellow

Write-Host ""
Write-Host "=== Build pipeline complete ===" -ForegroundColor Cyan
Write-Host "  Installer: $ReleaseDir\$InstallerName"
