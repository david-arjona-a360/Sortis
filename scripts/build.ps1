<#
.SYNOPSIS
    Full build pipeline: PyInstaller (onedir) -> staging -> Inno Setup installer.
.PARAMETER SkipBuild
    Skip PyInstaller build, use existing dist\SORTIS\.
.PARAMETER SkipPackage
    Stop after staging (do not run Inno Setup).
#>

param(
    [switch]$SkipBuild,
    [switch]$SkipPackage
)

$ErrorActionPreference = "Stop"

# ── Paths ─────────────────────────────────────────────────────────────────
$ProjectRoot    = Resolve-Path "$PSScriptRoot\.."
$DistDir        = Join-Path $ProjectRoot "dist"
$BuildDir       = Join-Path $ProjectRoot "build"
$SpecFile       = Join-Path $ProjectRoot "build.spec"
$StagingDir     = Join-Path $ProjectRoot "release\staging"
$ReleaseDir     = Join-Path $ProjectRoot "release"
$SetupIss       = Join-Path $PSScriptRoot "setup.iss"

$AppName        = "SORTIS"
$AppVersion     = "2.0.0"
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

# ── Phase 2: Stage ───────────────────────────────────────────────────────
Write-Host "=== Phase 2: Stage ===" -ForegroundColor Green

$sourceDir = Join-Path $DistDir "SORTIS"
if (-not (Test-Path $sourceDir)) {
    throw "Source directory not found at $sourceDir. Run without -SkipBuild first."
}

Write-Host "  -> Creating staging directory: $StagingDir"
if (Test-Path $StagingDir) { Remove-Item -Recurse -Force $StagingDir }
New-Item -ItemType Directory -Path $StagingDir -Force | Out-Null

Write-Host "  -> Copying runtime files ..."
Copy-Item -Path "$sourceDir\*" -Destination $StagingDir -Recurse -Force

Write-Host "  -> Copying config ..."
$ConfigDir = Join-Path $ProjectRoot "config"
$ConfigDest = Join-Path $StagingDir "config"
if (Test-Path $ConfigDir) {
    if (Test-Path $ConfigDest -PathType Leaf) { Remove-Item -Force $ConfigDest }
    New-Item -ItemType Directory -Path $ConfigDest -Force | Out-Null
    Copy-Item -Path "$ConfigDir\*" -Destination $ConfigDest -Recurse -Force
    Write-Host "  -> Config staged: config\dept_colors.json" -ForegroundColor Yellow
} else {
    Write-Warning "  -> config directory not found at $ConfigDir - skipping"
}

$stagedExe = Join-Path $StagingDir $ExeName
if (-not (Test-Path $stagedExe)) {
    throw "Staging validation failed: $stagedExe missing."
}
Write-Host "  -> Staged: $((Get-ChildItem -Recurse $StagingDir | Measure-Object).Count) files" -ForegroundColor Yellow
Write-Host ""

# ── Phase 3: Package (Inno Setup) ────────────────────────────────────────
if (-not $SkipPackage) {
    Write-Host "=== Phase 3: Package ===" -ForegroundColor Green

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
} else {
    Write-Host "=== Phase 3: SKIPPED (--SkipPackage) ===" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Build pipeline complete ===" -ForegroundColor Cyan
Write-Host "  Staging  : $StagingDir"
Write-Host "  Installer: $ReleaseDir\$InstallerName"
