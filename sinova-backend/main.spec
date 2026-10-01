# -*- mode: python ; coding: utf-8 -*-
import glob
import os
import re
import subprocess
import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

datas, binaries, hiddenimports = collect_all('tomopy')

conda_prefix = os.environ.get('CONDA_PREFIX', '')

if sys.platform == 'win32':
    pattern = os.path.join(conda_prefix, 'Library', 'bin', 'tomo-*.dll')
else:
    pattern = os.path.join(conda_prefix, 'lib', 'libtomo-*.so')

tomo_libs = glob.glob(pattern)
assert len(tomo_libs) >= 4, f"TomoPy shared libraries not found: {pattern}"

for lib in tomo_libs:
    binaries.append((lib, '.'))

# Linux: also bundle every dependency of the TomoPy libs that lives in the conda prefix
if sys.platform.startswith('linux'):
    env = dict(os.environ)
    env['LD_LIBRARY_PATH'] = os.path.join(conda_prefix, 'lib')
    already = {os.path.basename(src) for src, _ in binaries}
    for lib in tomo_libs:
        out = subprocess.run(['ldd', lib], env=env, capture_output=True, text=True).stdout
        for line in out.splitlines():
            m = re.search(r'=>\s+(\S+)\s+\(0x', line)
            if not m:
                continue
            dep = os.path.realpath(m.group(1))
            name = os.path.basename(m.group(1))
            if dep.startswith(os.path.realpath(conda_prefix)) and name not in already:
                binaries.append((m.group(1), '.'))
                already.add(name)
                print(f"[main.spec] bundling dependency: {name}")

hiddenimports.extend([
    'uvicorn.logging',
    'uvicorn.loops.auto',
    'uvicorn.protocols.http.auto',
])

a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(SPECPATH, 'patch_ctypes_hook.py')],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='main',
)