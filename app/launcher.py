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

DEFAULT_PORT = 5057

# 本服务的网页指纹：index 页 <title> 里的稳定中文标识，用于 M2 判断端口上是不是自己人。
SERVICE_FINGERPRINT = "产品详情套图工具"


def _reuse_running_instance(port):
    """M2: 默认端口上已有本服务实例在跑时返回 True（调用方直接开浏览器退出，不再起新实例）。

    只认默认端口；连接失败/超时/指纹不匹配一律返回 False，走正常启动流程。
    """
    if port != DEFAULT_PORT:
        return False
    try:
        import urllib.request as _urllib
        with _urllib.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as _r:
            if _r.status != 200:
                return False
            _body = _r.read(65536).decode("utf-8", "replace")
        return SERVICE_FINGERPRINT in _body
    except Exception:
        return False


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

    port = DEFAULT_PORT
    port_explicit = False
    no_browser = False
    i = 0
    while i < len(argv):
        if argv[i] == "--port" and i + 1 < len(argv):
            try:
                port = int(argv[i + 1])
            except ValueError:
                # L3: 非法端口给人话，不抛堆栈
                print("[launcher] --port 必须是数字", file=sys.stderr)
                sys.exit(2)
            port_explicit = True
            i += 2
        elif argv[i] == "--no-browser":
            no_browser = True
            i += 1
        else:
            i += 1

    # M2: 第二次双击时默认端口上已有本服务，直接开浏览器退出，不再起新实例。
    if not port_explicit and _reuse_running_instance(port):
        url = f"http://127.0.0.1:{port}/"
        if not no_browser:
            webbrowser.open(url)
            print(f"[launcher] 检测到已有实例在运行，已在浏览器打开 {url}")
        else:
            print(f"[launcher] 检测到已有实例在运行：{url}")
        sys.exit(0)

    port = find_port(port)

    t = threading.Thread(target=server_main, args=(["--port", str(port)],),
                         daemon=True)
    t.start()

    # 等服务真正就绪再开浏览器：onefile 首次解包 + Defender 扫描经常超过 1 秒，
    # 固定 sleep 会让浏览器先看到"无法连接"（军师评审 M1）。
    import socket as _socket
    import time as _time
    ready = False
    for _ in range(20):
        try:
            with _socket.create_connection(("127.0.0.1", port), timeout=1):
                ready = True
                break
        except OSError:
            _time.sleep(1.0)
    url = f"http://127.0.0.1:{port}/"
    if not ready:
        print(f"[launcher] 本地服务启动超时，请手动打开 {url}")
        sys.exit(1)
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
