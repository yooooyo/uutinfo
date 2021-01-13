# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['updater.py'],
             pathex=['D:\\Work\\HP_Project\\uutinfo', 
        'C:\\Program Files (x86)\\Windows Kits\\10\\Redist\\ucrt\\DLLs\\x86',
        'C:\\Program Files (x86)\\Windows Kits\\10\\Redist\\ucrt\\DLLs\\arm',
        'C:\\Program Files (x86)\\Windows Kits\\10\\Redist\\ucrt\\DLLs\\x64'],
             binaries=[],
             datas=[('o365_token.txt', '.'),('credentials.json', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='updater',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True , uac_admin=True)
