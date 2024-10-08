# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['agent-smith.py'],
    pathex=[],
    binaries=[],
    datas=[('./application/static/*', './application/static'), ('./application/config/nginx/*', './application/config/nginx'), ('./application/gui/resources/agent-white.png', 'u./application/gui/resources'), ('./application/gui/resources/agent-green.png', './application/gui/resources'), ('./application/games/*.py', './application/games'), ('./application/games/resources/*', './application/games/resources'), ('./application/alembic/alembic.ini', './application/alembic'), ('./application/alembic/env.py', './application/alembic'), ('./application/alembic/script.py.mako', './application/alembic'), ('./application/alembic/versions/*.py', './application/alembic/versions')],
    hiddenimports=['xml.etree.ElementTree', 'telnetlib'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='agent-smith',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['application\\gui\\resources\\agent-black.ico'],
)
