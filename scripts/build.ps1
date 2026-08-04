<#
.SYNOPSIS
    Build pipeline: PyInstaller (onedir) -> signed EXE -> ZIP distribution.
    Optionally builds an Inno Setup installer (see -Inno).
    No staging folder: packages directly from dist\SORTIS + config.
.PARAMETER SkipBuild
    Skip PyInstaller build, use existing dist\SORTIS\.
.PARAMETER SkipSign
    Do not sign the EXE/installer (unsigned output).
.PARAMETER Inno
    Also build the Inno Setup installer. NOTE: currently flagged by
    Microsoft Defender ML (Wacatac.F!ml) on this network; use ZIP instead
    until IT deploys an allow rule or a trusted code-signing cert.
.PARAMETER SigningThumbprint
    Thumbprint of the code-signing certificate to use. Default: first
    code-signing cert with private key in CurrentUser\My / LocalMachine\My.
#>

param(
    [switch]$SkipBuild,
    [switch]$SkipSign,
    [switch]$Inno,
    [string]$SigningThumbprint
)

$ErrorActionPreference = "Stop"

# ── Helpers ───────────────────────────────────────────────────────────────
function Get-CodeSigningCert {
    param([string]$Thumbprint)
    if ($Thumbprint) {
        $c = Get-ChildItem Cert:\CurrentUser\My, Cert:\LocalMachine\My -ErrorAction SilentlyContinue |
             Where-Object { $_.Thumbprint -eq $Thumbprint } | Select-Object -First 1
        if (-not $c) { throw "Certificate with thumbprint $Thumbprint not found." }
        return $c
    }
    $c = Get-ChildItem Cert:\CurrentUser\My, Cert:\LocalMachine\My -ErrorAction SilentlyContinue |
         Where-Object { $_.HasPrivateKey -and ($_.EnhancedKeyUsageList -match 'Code Signing') } |
         Select-Object -First 1
    if (-not $c) { throw "No code-signing certificate found in the certificate store." }
    return $c
}

function Test-SelfSigned {
    param([System.Security.Cryptography.X509Certificates.X509Certificate2]$Cert)
    return ($Cert.Subject -eq $Cert.Issuer)
}

function Sign-File {
    param([string]$Path, [System.Security.Cryptography.X509Certificates.X509Certificate2]$Cert)
    if (Test-SelfSigned -Cert $Cert) {
        Write-Host "  -> SKIPPED signing: certificate '$($Cert.Subject)' is SELF-SIGNED." -ForegroundColor Red
        Write-Host "     Self-signed signatures provide NO AV reputation and can make ML detectors" -ForegroundColor Red
        Write-Host "     MORE suspicious (signature-spoof trait). Use -SkipSign or a publicly" -ForegroundColor Red
        Write-Host "     trusted code-signing cert (Azure Trusted Signing)." -ForegroundColor Red
        return
    }
    $sig = $null
    foreach ($ts in @('http://timestamp.digicert.com', 'http://timestamp.comodoca.com', $null)) {
        try {
            if ($ts) {
                $sig = Set-AuthenticodeSignature -FilePath $Path -Certificate $Cert -HashAlgorithm SHA256 -TimestampServer $ts
            } else {
                $sig = Set-AuthenticodeSignature -FilePath $Path -Certificate $Cert -HashAlgorithm SHA256
            }
            if ($sig.Status -eq 'Valid' -or ($sig.Status -eq 'UnknownError' -and $sig.SignatureType -eq 'Authenticode')) {
                break
            }
            throw "Signing returned status $($sig.Status)"
        } catch {
            if (-not $ts) { throw "Signing failed for $Path : $_" }
            Write-Host "  -> Timestamp server $ts unreachable, retrying without timestamp..." -ForegroundColor Gray
        }
    }
    if ($sig.Status -eq 'Valid') {
        Write-Host "  -> Signed: $Path" -ForegroundColor Yellow
        return
    }
    Write-Host "  -> Signed (chain untrusted, expected with self-signed cert): $Path" -ForegroundColor DarkYellow
    Write-Host "     Signature embedded: $($sig.SignerCertificate.Subject)" -ForegroundColor DarkYellow
}

function New-ZipPackage {
    param([string]$DistSub, [string]$ConfigDir, [string]$OutputZip)
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $stage = Join-Path ([System.IO.Path]::GetTempPath()) ("SORTIS_pkg_" + [System.Guid]::NewGuid().ToString("N"))
    try {
        New-Item -ItemType Directory -Path $stage | Out-Null
        Copy-Item -Recurse "$DistSub\*" $stage
        New-Item -ItemType Directory -Path (Join-Path $stage "config") | Out-Null
        Copy-Item -Recurse "$ConfigDir\*" (Join-Path $stage "config")
        [System.IO.Compression.ZipFile]::CreateFromDirectory($stage, $OutputZip, [System.IO.Compression.CompressionLevel]::Optimal, $false)
    } finally {
        if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
    }
    Write-Host "  -> ZIP created: $OutputZip" -ForegroundColor Yellow
}

# ── Paths ─────────────────────────────────────────────────────────────────
$ProjectRoot    = Resolve-Path "$PSScriptRoot\.."
$DistDir        = Join-Path $ProjectRoot "dist"
$BuildDir       = Join-Path $ProjectRoot "build"
$SpecFile       = Join-Path $ProjectRoot "build.spec"
$ReleaseDir     = Join-Path $ProjectRoot "release"
$ConfigDir      = Join-Path $ProjectRoot "config"
$SetupIss       = Join-Path $PSScriptRoot "setup.iss"

$AppName        = "SORTIS"
$AppVersion     = "2.0.1"
$ExeName        = "SORTIS.exe"
$ZipName        = "${AppName}_v${AppVersion}.zip"
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

    if (-not $SkipSign) {
        Write-Host "  -> Signing EXE..."
        $cert = Get-CodeSigningCert $SigningThumbprint
        Sign-File -Path $exePath -Cert $cert
    }
    Write-Host ""
} else {
    Write-Host "=== Phase 1: SKIPPED (--SkipBuild) ===" -ForegroundColor Gray
}

# ── Phase 2: Package (ZIP) ───────────────────────────────────────────────
Write-Host "=== Phase 2: Package (ZIP) ===" -ForegroundColor Green

$prevZip = Join-Path $ReleaseDir $ZipName
if (Test-Path $prevZip) { Remove-Item -Force $prevZip }

$distSub = Join-Path $DistDir "SORTIS"
$exePath = Join-Path $distSub $ExeName
if (-not (Test-Path $exePath)) {
    throw "Build output not found at $exePath. Run without -SkipBuild first."
}

New-ZipPackage -DistSub $distSub -ConfigDir $ConfigDir -OutputZip $prevZip

# ── Phase 3: Package (Inno Setup installer, optional) ────────────────────
if ($Inno) {
    Write-Host "=== Phase 3: Package (Inno Setup) ===" -ForegroundColor Green

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

    if (-not $SkipSign) {
        Write-Host "  -> Signing installer..."
        $cert = Get-CodeSigningCert $SigningThumbprint
        Sign-File -Path $prevInstaller -Cert $cert
    }
}

Write-Host ""
Write-Host "=== Build pipeline complete ===" -ForegroundColor Cyan
Write-Host "  ZIP       : $ReleaseDir\$ZipName"
if ($Inno) { Write-Host "  Installer : $ReleaseDir\$InstallerName" }
