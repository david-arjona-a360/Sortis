# -*- mode: python ; coding: utf-8 -*-
#
# SORTIS - PyInstaller build spec.
#
# Key hardening decisions (see repo analysis):
#   * onedir (COLLECT) -- onefile is far more likely to trip AV ML heuristics.
#   * upx=False -- UPX-packed binaries are a strong Wacatac/ML trigger.
#   * Aggressive `excludes` -- prevents PyInstaller hooks from dragging unused
#     Qt modules, numpy, PIL, pywin32/WMI, charset_normalizer (mypyc), and the
#     OpenSSL DLLs that Qt6Network would pull in.
#   * Post-analysis binary filter -- removes ANGLE/OpenGL software renderer
#     DLLs that the PySide6 hook collects unconditionally (the app is a pure
#     QPainter/raster app and never needs them).
#
# NOTE: This spec is only as clean as the environment it runs in. Always build
# from a dedicated venv created with `requirements-build.txt`. Never build in a
# shared/global Python that has extra packages installed (numpy, requests,
# pywin32, Django, etc.) and never let vendor dirs (e.g. "C:\Program Files\HP\
# HP One Agent") sit on PATH -- PyInstaller resolves DLL dependencies through
# PATH and will bundle copies of them into dist\SORTIS\_internal\.
import os


def _drop_unneeded_binaries(binaries):
    """Filter out hook-collected binaries the app never uses.

    Returned entries keep PyInstaller's tuple format
    (dest_name, source_path, typecode) with typecode == 'BINARY'.
    """
    blocked = {
        # Qt ANGLE + OpenGL software renderer (20 MB). SORTIS renders via
        # QPainter (raster); these are only needed for QOpenGLWidget.
        'opengl32sw.dll',
        'libEGL.dll',
        'libGLESv2.dll',
        'd3dcompiler_47.dll',
        # Qt Network / OpenSSL: excluded via 'PySide6.QtNetwork' too, but this
        # is a second layer of defense.
        'libcrypto-3.dll',
        'libssl-3.dll',
        'libcrypto-3-x64.dll',
        'libssl-3-x64.dll',
        # Orphaned Qt DLLs: PySide6 6.x links every .pyd against the whole Qt
        # library set, so the QtCore hook collects Qt DLLs whose Python modules
        # were already excluded from the PYZ (nothing at load time references
        # them). Only Core/Gui/Widgets/PrintSupport are needed by SORTIS.
        'qt6network.dll',
        'qt6opengl.dll',
        'qt6pdf.dll',
        'qt6qml.dll',
        'qt6qmlmeta.dll',
        'qt6qmlmodels.dll',
        'qt6qmlworkerscript.dll',
        'qt6quick.dll',
        'qt6quickwidgets.dll',
        'qt6quicktemplates2.dll',
        'qt6quickcontrols2impl.dll',
        'qt6svg.dll',
        'qt6virtualkeyboard.dll',
        'qt6webenginecore.dll',
        'qt6webenginewidgets.dll',
    }
    kept = []
    for item in binaries:
        dest, src, typecode = item
        if typecode != 'BINARY':
            kept.append(item)
            continue
        base = os.path.basename(dest).lower()
        if base in blocked:
            continue
        low_dest = dest.replace('\\', '/').lower()
        if low_dest.startswith('pyside6/plugins/'):
            if any(dead in low_dest for dead in (
                '/platforminputcontexts/',      # QtVirtualKeyboard
                '/generic/qtuiotouchplugin.dll',
                '/iconengines/qsvgicon.dll',
                '/imageformats/qpdf.dll',
                '/imageformats/qsvg.dll',
                '/imageformats/qicns.dll',
                '/imageformats/qtga.dll',
                '/imageformats/qtiff.dll',
                '/imageformats/qwbmp.dll',
                '/platforms/qdirect2d.dll',
                '/platforms/qminimal.dll',
                '/platforms/qoffscreen.dll',
            )):
                continue
        kept.append(item)
    return kept


def _drop_unneeded_datas(datas):
    """Filter out Qt plugins/translations belonging to dead modules."""
    def _dead(dest):
        low = dest.replace('\\', '/').lower()
        # Plugin files pulled by the excluded Qt modules.
        if low.startswith('pyside6/plugins/'):
            for dead in (
                '/platforminputcontexts/',      # QtVirtualKeyboard
                '/generic/qtuiotouchplugin.dll',
                '/iconengines/qsvgicon.dll',
                '/imageformats/qpdf.dll',
                '/imageformats/qsvg.dll',
                '/imageformats/qicns.dll',
                '/imageformats/qtga.dll',
                '/imageformats/qtiff.dll',
                '/imageformats/qwbmp.dll',
                '/platforms/qdirect2d.dll',
                '/platforms/qminimal.dll',
                '/platforms/qoffscreen.dll',
            ):
                if dead in low:
                    return True
        # Translations: SORTIS installs no QTranslator, so every .qm is dead
        # weight. Keep the Spanish + English base bundles as insurance only.
        if low.startswith('pyside6/translations/'):
            base = low.rsplit('/', 1)[-1]
            return base not in ('qtbase_es.qm', 'qtbase_en.qm')
        return False

    return [item for item in datas if not _dead(item[0])]


a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'openpyxl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # --- Stdlib that is never needed by this app --------------------
        'tkinter', 'test', 'pydoc', 'pydoc_data', 'distutils', 'json.tool',
        'lib2to3', 'multiprocessing', 'pdb', 'sqlite3', 'telnetlib',
        'turtle', 'turtledemo', 'venv', 'webbrowser', 'xmlrpc', 'pickle',
        # --- Qt modules NOT used by SORTIS -------------------------------
        # QtCore/QtGui/QtWidgets/QtPrintSupport are the ONLY ones imported.
        'PySide6.QtNetwork',          # pulls Qt6Network.dll + OpenSSL
        'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickWidgets',
        'PySide6.QtQuick3D', 'PySide6.QtQuickControls2', 'PySide6.QtQuickTest',
        'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
        'PySide6.QtSvg', 'PySide6.QtSvgWidgets',
        'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets',
        'PySide6.QtVirtualKeyboard', 'PySide6.QtVirtualKeyboardSettings',
        'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineQuick', 'PySide6.QtWebSockets', 'PySide6.QtWebView',
        'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
        'PySide6.QtCharts', 'PySide6.QtGraphs', 'PySide6.QtGraphsWidgets',
        'PySide6.QtDataVisualization', 'PySide6.Qt3DCore', 'PySide6.Qt3DRender',
        'PySide6.Qt3DInput', 'PySide6.Qt3DLogic', 'PySide6.Qt3DAnimation',
        'PySide6.Qt3DExtras', 'PySide6.QtBluetooth', 'PySide6.QtNfc',
        'PySide6.QtPositioning', 'PySide6.QtLocation', 'PySide6.QtSensors',
        'PySide6.QtSerialPort', 'PySide6.QtSerialBus', 'PySide6.QtSql',
        'PySide6.QtTest', 'PySide6.QtXml', 'PySide6.QtDBus', 'PySide6.QtHelp',
        'PySide6.QtUiTools', 'PySide6.QtAxContainer', 'PySide6.QtStateMachine',
        'PySide6.QtTextToSpeech', 'PySide6.QtRemoteObjects', 'PySide6.QtScxml',
        'PySide6.QtDesigner', 'PySide6.QtDesignerComponents',
        'PySide6.QtHttpServer', 'PySide6.QtNetworkAuth',
        # --- Packages NOT used by SORTIS (openpyxl imports numpy and PIL
        #     inside try/except ImportError, so excluding is safe) --------
        'numpy', 'PIL', 'defusedxml', 'charset_normalizer',
        'requests', 'urllib3', 'certifi', 'idna', 'cryptography',
        # --- Windows API / WMI / COM packages -----------------------------
        'win32', 'win32pdh', 'win32api', 'win32con', 'win32evtlog',
        'win32security', 'pywintypes', 'pywin32', 'pythoncom',
        'comtypes', 'wmi',
    ],
    noarchive=False,
    optimize=1,
)

# Second layer of defense: strip hook-collected binaries we never use.
a.binaries = _drop_unneeded_binaries(a.binaries)
a.datas = _drop_unneeded_datas(a.datas)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SORTIS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/SORTIS.ico',
    version='SORTIS_version_info.txt',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SORTIS',
)
