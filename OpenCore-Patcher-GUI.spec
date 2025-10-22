# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import time
import platform
import subprocess
import importlib

from pathlib import Path

from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.osx import BUNDLE
from PyInstaller.building.build_main import Analysis

sys.path.append(os.path.abspath(os.getcwd()))

from opencore_legacy_patcher import constants

block_cipher = None

datas = [
   ('payloads.dmg', '.'),
   ('Universal-Binaries.dmg', '.'),
]

if Path("DortaniaInternalResources.dmg").exists():
   datas.append(('DortaniaInternalResources.dmg', '.'))

def _is_fat_binary(path: Path) -> bool:
   """
   Returns True when the provided binary contains both x86_64 and arm64 slices.
   """
   try:
      output = subprocess.check_output(["lipo", "-info", str(path)], stderr=subprocess.STDOUT).decode(errors="ignore")
   except Exception:
      return False
   return ("Non-fat" not in output) and ("x86_64" in output) and ("arm64" in output)


def _detect_target_arch() -> str:
   """
   Select universal build only when the interpreter and core native
   extensions are true fat binaries. Allow manual override via
   PYINSTALLER_TARGET_ARCH.
   """
   override = os.environ.get("PYINSTALLER_TARGET_ARCH")
   if override:
      return override

   if not _is_fat_binary(Path(sys.executable)):
      return platform.machine()

   for module_name in ("wx._core", "wx._adv"):
      try:
         module = importlib.import_module(module_name)
      except Exception:
         continue
      module_path = Path(getattr(module, "__file__", ""))
      if module_path.suffix == ".so" and not _is_fat_binary(module_path):
         return platform.machine()

   return "universal2"

target_arch = _detect_target_arch()

a = Analysis(['OpenCore-Patcher-GUI.command'],
             pathex=[],
             binaries=[],
             datas=datas,
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure,
          a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='OpenCore-Patcher',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=target_arch,
          codesign_identity=None,
          entitlements_file=None)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='OpenCore-Patcher')

app = BUNDLE(coll,
             name='OpenCore-Patcher.app',
             icon="payloads/Icon/AppIcons/OC-Patcher.icns",
             bundle_identifier="com.dortania.opencore-legacy-patcher",
             info_plist={
                "CFBundleName": "OpenCore Legacy Patcher",
                "CFBundleVersion": constants.Constants().patcher_version,
                "CFBundleShortVersionString": constants.Constants().patcher_version,
                "NSHumanReadableCopyright": constants.Constants().copyright_date,
                "LSMinimumSystemVersion": "10.10.0",
                "NSRequiresAquaSystemAppearance": False,
                "NSHighResolutionCapable": True,
                "Build Date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "BuildMachineOSBuild": subprocess.run(["/usr/bin/sw_vers", "-buildVersion"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode().strip(),
                "NSPrincipalClass": "NSApplication",
             })
