# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：产品详情套图工具 → Windows 单文件 EXE。

说明：
- 入口 app/launcher.py（正常模式起 Flask+开浏览器；--pipeline-worker 模式供内部跑 pipeline 脚本）。
- pipeline/*.py 以 data 形式打包（launcher 用 runpy 执行，不走 import），prompts/*.yaml 模板库一并带入。
- products/ 输出目录不在包内：EXE 运行时在 EXE 所在目录下创建。
- 在 GitHub Actions windows-latest 上执行：pyinstaller build.spec
- 军师评审 L7：已删掉纯默认值的样板参数，只保留非默认项。
"""

a = Analysis(
    ['app/launcher.py'],
    datas=[
        ('pipeline', 'pipeline'),
        ('app/templates', 'app/templates'),
        ('app/static', 'app/static'),
    ],
    hiddenimports=[
        'flask', 'jinja2', 'werkzeug', 'markupsafe', 'itsdangerous', 'click',
        'yaml', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont',
    ],
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='套图工坊',
    console=True,  # 首版保留控制台，方便看日志排错
)
