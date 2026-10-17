# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：产品详情套图工具 → Windows 单文件 EXE。

说明：
- 入口 app/launcher.py（正常模式起 Flask+开浏览器；--pipeline-worker 模式供内部跑 pipeline 脚本）。
- pipeline/*.py 以 data 形式打包（launcher 用 runpy 执行，不走 import），prompts/*.yaml 模板库一并带入。
- products/ 输出目录不在包内：EXE 运行时在 EXE 所在目录下创建。
- 在 GitHub Actions windows-latest 上执行：pyinstaller build.spec
"""

block_cipher = None

a = Analysis(
    ['app/launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('pipeline', 'pipeline'),
        ('app/templates', 'app/templates'),
        ('app/static', 'app/static'),
    ],
    hiddenimports=[
        'flask', 'jinja2', 'werkzeug', 'markupsafe', 'itsdangerous', 'click',
        'yaml', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='套图工坊',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 首版保留控制台，方便看日志排错
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
