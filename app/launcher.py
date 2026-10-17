#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EXE 入口：起 Flask 本地服务并自动打开浏览器。

特殊模式（供冻结 EXE 内部调用）：
  --pipeline-worker <脚本相对路径> [参数...]  以 runpy 方式执行 pipeline 脚本
    （PyInstaller 单文件里 sys.executable 是 EXE 本体，不能直接当 python 用）
"""

import os
import sys
import threading
import webbrowser


def _project_root():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _worker_mode(args):
    """--pipeline-worker pipeline/run.py [args...]"""
    if len(args) < 1:
        sys.exit("[launcher] --pipeline-worker 需要脚本相对路径")
    rel = args[0].replace("/", os.sep)
    root = _project_root()
    script = os.path.join(root, rel)
    if not os.path.isfile(script):
        sys.exit(f"[launcher] 脚本不存在: {script}")
    sys.path.insert(0, os.path.dirname(script))
    sys.argv = [script] + args[1:]
    import runpy
    runpy.run_path(script, run_name="__main__")


def main():
    # Windows 控制台默认编码常为 cp1252/cp936，打印中文帮助/日志会炸。
    # 冻结 EXE 里统一切到 UTF-8，实在显示不了就用 ? 代替，保证不崩。
    for _s in (sys.stdout, sys.stderr):
        try:
            if _s is not None and hasattr(_s, "reconfigure"):
                _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    argv = sys.argv[1:]

    if "--help" in argv or "-h" in argv:
        print("产品详情套图工具（本地网页版）\n"
              "\n"
              "用法: 套图工坊.exe [--port 5057] [--no-browser]\n"
              "\n"
              "  双击直接运行：启动本地网页服务并自动打开浏览器。\n"
              "  --port PORT     网页端口（默认 5057，被占用自动 +1）\n"
              "  --no-browser    不自动打开浏览器（只起服务）\n")
        return

    if argv and argv[0] == "--pipeline-worker":
        _worker_mode(argv[1:])
        return

    # 正常模式：起服务 + 开浏览器
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from server import main as server_main, find_port
    except ImportError:  # python -m app.launcher 方式启动
        from app.server import main as server_main, find_port

    port = 5057
    no_browser = False
    i = 0
    while i < len(argv):
        if argv[i] == "--port" and i + 1 < len(argv):
            port = int(argv[i + 1])
            i += 2
        elif argv[i] == "--no-browser":
            no_browser = True
            i += 1
        else:
            i += 1
    port = find_port(port)
    url = f"http://127.0.0.1:{port}/"

    t = threading.Thread(target=server_main, args=(["--port", str(port)],),
                         daemon=True)
    t.start()

    import time
    time.sleep(1.0)
    if not no_browser:
        webbrowser.open(url)
    print(f"[launcher] 已打开 {url}")
    print("[launcher] 按 Ctrl+C 退出。")
    try:
        t.join()
    except KeyboardInterrupt:
        print("\n[launcher] 已退出。")


if __name__ == "__main__":
    main()
