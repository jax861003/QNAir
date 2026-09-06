#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描全部上游文件夹，合并输出根目录的 QNAir-all.txt 与 sources.json。

有效性规则（与源项目一致）：数据文件首行的时间戳在 24 小时以内
才视为活跃；超期来源不再进入合并结果，但在 sources.json 中保留
状态供页面展示。

用法：python scripts/merge.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (FRESH_HOURS, SOURCES, bj_compact, bj_iso,
                    file_header_time, is_fresh, reparse_nodes, source_file)


def collect():
    """扫描各上游文件夹，返回 (状态列表, 去重后的合并节点列表)"""
    report, all_nodes = [], []
    seen = set()
    for src in SOURCES:
        path = source_file(src)
        nodes = reparse_nodes(path, src["code"]) if path.exists() else []
        t = file_header_time(path) if path.exists() else None
        active = bool(nodes) and is_fresh(t)
        if active:
            for n in nodes:
                if n.key not in seen:
                    seen.add(n.key)
                    all_nodes.append((src["code"], n))
        report.append({
            "name": src["name"],
            "label": src["label"],
            "code": src["code"],
            "path": f"{src['folder']}/all.txt",
            "entries": len(nodes),
            "active": active,
            "last_updated": t.isoformat() if t else None,
        })
    return report, all_nodes


def merge_main():
    report, merged = collect()

    # ---- 全量合并：序号连续编号 ----
    lines = [n.line(code, i) for i, (code, n) in enumerate(merged, 1)]
    out = Path(__file__).resolve().parent.parent / "QNAir-all.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    active = [r for r in report if r["active"]]
    meta = {
        "generated_at": bj_iso(),
        "generated_compact": bj_compact(),
        "fresh_hours": FRESH_HOURS,
        "total_entries": len(merged),
        "active_sources": len(active),
        "format": "IP:端口#QNAir-简称 | 地区 | 序号",
        "sources": report,
    }
    meta_path = out.parent / "sources.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                         encoding="utf-8")

    print(f"[完成] 活跃上游 {len(active)}/{len(SOURCES)}，"
          f"合并去重后 {len(merged)} 条 -> QNAir-all.txt")
    return meta


if __name__ == "__main__":
    meta = merge_main()
    if not meta["total_entries"]:
        print("[警告] 没有任何 24h 内活跃的上游数据")
        sys.exit(1)
