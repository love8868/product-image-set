#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S0 素材入库：Shopify .json -> product_raw.json，图片下载到 raw/。

Usage:
  python3 pipeline/ingest.py --handle <product-handle> [--site https://manhattanproducts.eu]
  python3 pipeline/ingest.py --url https://manhattanproducts.eu/products/<handle>
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "product-image-set/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "product-image-set/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
        f.write(resp.read())


def main():
    ap = argparse.ArgumentParser(description="S0: ingest product JSON + images")
    ap.add_argument("--handle", help="Shopify product handle")
    ap.add_argument("--url", help="full product page URL (handle extracted)")
    ap.add_argument("--site", default="https://manhattanproducts.eu")
    ap.add_argument("--workdir", help="default: products/<handle>/")
    args = ap.parse_args()

    handle = args.handle
    if args.url:
        m = re.search(r"/products/([a-z0-9\-]+)", args.url)
        if not m:
            sys.exit(f"cannot extract handle from url: {args.url}")
        handle = m.group(1)
    if not handle:
        sys.exit("--handle or --url required")

    workdir = args.workdir or os.path.join(BASE_DIR, "products", handle)
    raw_dir = os.path.join(workdir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    json_url = f"{args.site.rstrip('/')}/products/{handle}.json"
    print(f"[ingest] GET {json_url}")
    try:
        data = fetch_json(json_url)
    except urllib.error.HTTPError as e:
        sys.exit(f"[ingest] HTTP {e.code} 拉取失败：{json_url}\n"
                 "检查 --handle/--site 是否正确，确认该 Shopify 站点 /products/<handle>.json 可访问")
    except urllib.error.URLError as e:
        sys.exit(f"[ingest] 网络错误（{e.reason}），检查网络连接与 --site")
    except json.JSONDecodeError:
        sys.exit(f"[ingest] 返回内容不是 JSON：{json_url}（该站点可能不是 Shopify 架构）")
    product = data.get("product", data)

    with open(os.path.join(workdir, "product_raw.json"), "w", encoding="utf-8") as f:
        json.dump(product, f, ensure_ascii=False, indent=2)

    images = product.get("images") or []
    print(f"[ingest] title: {product.get('title')}")
    print(f"[ingest] images: {len(images)}")
    for i, im in enumerate(images, 1):
        src = im.get("src", "")
        # strip size params, keep version for cache-busting
        dest = os.path.join(raw_dir, f"{i:02d}.jpg")
        try:
            download(src, dest)
            print(f"[ingest]   {i:02d}.jpg <- {src[:80]}...")
        except Exception as e:  # noqa: BLE001 - keep ingesting the rest
            print(f"[ingest]   !! failed {src}: {e}")

    print(f"[ingest] done -> {workdir}")


if __name__ == "__main__":
    main()
