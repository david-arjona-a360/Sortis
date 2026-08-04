<#
.SYNOPSIS
    Experimental Nuitka build path for SORTIS (onedir/standalone).

    Nuitka compiles Python to native C code, which produces a structurally
    very different binary than PyInstaller. This is a fallback migration path
    if Microsoft Defender keeps flagging the PyInstaller build.

.NOTES
    PREREQUISITES (not verified on this machine):
      * MSVC C++ build tools (Visual Studio Build Tools, "Desktop development
        with C++" workload). cl.exe MUST be findable via vswhere/devcmd.
      * Run from the clean build venv (installs Nuitka if missing).
      * First build is SLOW (30-60+ min) because shiboken/PySide6 bindings
        must be compiled. Subsequent builds are fast (ccache).
      * Build from a plain CMD/PowerShell without vendor dirs (e.g. HP One
        Agent) on PATH, exactly like the PyInstaller path.

    OUTCOME:
      dist_nuitka\SORTIS\  -> standalone app dir
      dist_nuitka\SORTIS.exe
#>

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
$VenvPy      = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPy)) {
    throw "Clean venv not found at $VenvPy. Create it first: .venv\Scripts\python -m venv .venv"
}

Write-Host "=== SORTIS Nuitka Build (experimental) ===" -ForegroundColor Cyan
Write-Host "Project root : $ProjectRoot"
Write-Host ""

# ── 1. Ensure Nuitka in the clean venv ─────────────────────────────────────
& $VenvPy -m pip show nuitka | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  -> Installing Nuitka into the clean venv..."
    & $VenvPy -m pip install nuitka
    if ($LASTEXITCODE -ne 0) { throw "Failed to install Nuitka." }
}

# ── 2. Build standalone ─────────────────────────────────────────────────────
# --standalone                      (onedir; NEVER --onefile -- AV ML trigger)
# --enable-plugin=pyside6           (collects Qt plugins/translations correctly)
# --windows-console-mode=disable    (GUI app)
# --nofollow-import-to              (mirror of build.spec excludes; PySide6
#                                    __init__ imports QtNetwork/Qml/Quick even
#                                    though SORTIS never uses them)
# --include-package=openpyxl        (PyInstaller needs hiddenimports; Nuitka
#                                    needs explicit include for conditional
#                                    imports)
# --assume-yes-for-downloads        (ccache, etc.)
Write-Host "  -> Running Nuitka (this takes a while)..."
& $VenvPy -m nuitka `
    --standalone `
    --enable-plugin=pyside6 `
    --windows-console-mode=disable `
    --windows-icon-from-ico="$ProjectRoot\assets\SORTIS.ico" `
    --windows-company-name="a360inc" `
    --windows-product-name="SORTIS" `
    --windows-product-version="2.0.1.0" `
    --nofollow-import-to="PySide6.QtNetwork" `
    --nofollow-import-to="PySide6.QtQml" `
    --nofollow-import-to="PySide6.QtQuick" `
    --nofollow-import-to="PySide6.QtPdf" `
    --nofollow-import-to="PySide6.QtSvg" `
    --nofollow-import-to="PySide6.QtOpenGL" `
    --nofollow-import-to="PySide6.QtVirtualKeyboard" `
    --nofollow-import-to="PySide6.QtWebEngineCore" `
    --nofollow-import-to="PySide6.QtMultimedia" `
    --nofollow-import-to="numpy" `
    --nofollow-import-to="PIL" `
    --nofollow-import-to="defusedxml" `
    --nofollow-import-to="charset_normalizer" `
    --nofollow-import-to="requests" `
    --nofollow-import-to="win32" `
    --nofollow-import-to="pywintypes" `
    --include-package=openpyxl `
    --assume-yes-for-downloads `
    "$ProjectRoot\src\main.py"
if ($LASTEXITCODE -ne 0) { throw "Nuitka build failed with exit code $LASTEXITCODE." }

Write-Host ""
Write-Host "  -> Output: $ProjectRoot\dist_nuitka\SORTIS\" -ForegroundColor Yellow
Write-Host "=== Nuitka build complete ===" -ForegroundColor Cyan
