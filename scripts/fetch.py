#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取单个上游并写入它自己的文件夹。

用法：python scripts/fetch.py <source_name>
示例：python scripts/fetch.py luoli

成功：刷新 <folder>/all.txt（首行带更新时间）。
失败：保留现有数据不覆盖；若现有数据仍在 24 小时内则继续可用，
      超过 24 小时的会在合并时被自动剔除。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (FETCHERS, file_header_time, get_source, is_fresh,
                    reparse_nodes, source_file, write_source_file)


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/fetch.py <source_name>")
        print("可选源: cmliu cmliu2 luoli lzj mia cfyes vvhan wetest "
              "uouin nirevil gslege zhixuanwang s5gy")
        sys.exit(2)

    name = sys.argv[1].strip().lower()
    src = get_source(name)
    if src is None:
        print(f"[错误] 未知数据源: {name}")
        sys.exit(2)

    label = src["label"]
    try:
        nodes = FETCHERS[src["type"]](src)
        if not nodes:
            raise RuntimeError("抓取结果为空")
    except Exception as e:
        # 抓取失败：不覆盖旧文件。旧数据 24h 内仍有效，超期由合并流程剔除。
        path = source_file(src)
        old = reparse_nodes(path, src["code"]) if path.exists() else []
        if old and is_fresh(file_header_time(path)):
            print(f"[回退] {label}: 抓取失败({e})，保留 {len(old)} 条 24h 内旧数据")
        else:
            print(f"[警告] {label}: 抓取失败({e})，且无 24h 内旧数据，本次跳过")
        return

    path = write_source_file(src, nodes)
    print(f"[OK] {label}: {len(nodes)} 条 -> {src['folder']}/all.txt")


if __name__ == "__main__":
    main()
