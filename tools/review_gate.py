#!/usr/bin/env python3
"""审核门：上游交付件进库前的机械初检。

分工约定：上游（任意执行者）只负责“按标准画 + 自测”，本脚本负责机械项，
人工负责“与标准原图/PDF 页逐项对照”这一层。机械项全绿且人工对照通过的件，
才允许合入 main 并上传。

用法：
    python3 tools/review_gate.py                 # 全库扫描，写 REVIEW-QUEUE.md
    python3 tools/review_gate.py S00012 S00019   # 只查指定件
    python3 tools/review_gate.py --render        # 额外调 QET 渲染抽查

判定分三档：
    PASS  机械项无问题，可进人工对照
    FIX   有确定缺陷（坐标制式、filling、单位标定作废、缺端口等），退回上游
    CHECK 有可疑项需人看（尺寸失控、连接点比例偏离、缺 README 字段）

退出码：全 PASS 为 0，否则 1。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYMBOLS = os.path.join(REPO, "symbols")
QET = os.path.expanduser("~/bin/qelectrotech")
OUT_MD = os.path.join(REPO, "REVIEW-QUEUE.md")

ALLOWED_FILLING = {"none", "black", "white", "#000000", "#ffffff"}
# 已作废的标定：旧稿写“1 格 = 34 单位”。实测 1 单位 = 0.254 mm，60 px 模数 = 20 单位。
STALE_UNIT_PATTERNS = [r"格\s*=\s*34"]
# 连接点直径 / 符号外框宽 的经验区间（标准页实测 0.13–0.16）
DOT_RATIO_RANGE = (0.05, 0.22)
OVERSIZE_UNITS = 400  # 400 单位 = 101.6 mm，A3 图面上单符号超过这个尺寸基本是失控


def half_grid_ok(v: float) -> bool:
    """坐标必须是整数或半格（x.5）。"""
    return abs(v * 2 - round(v * 2)) < 1e-6


def scan(elmt_path: str) -> dict:
    txt = open(elmt_path, encoding="utf-8").read()
    root = ET.fromstring(txt)
    info = root.find(".//informations")
    info_text = " ".join("".join(info.itertext()).split()) if info is not None else ""
    return {"root": root, "info": info_text, "raw": txt}


def check_symbol(sym_dir: str, sym_id: str) -> dict:
    res = {"id": sym_id, "fix": [], "check": []}
    elmt = os.path.join(sym_dir, f"{sym_id}.elmt")
    if not os.path.exists(elmt):
        alt = [f for f in os.listdir(sym_dir) if f.endswith(".elmt")]
        if not alt:
            res["fix"].append("缺 .elmt")
            return res
        elmt = os.path.join(sym_dir, alt[0])
    for f, label in (("README.md", "README.md"), ("LICENSE", "LICENSE")):
        if not os.path.exists(os.path.join(sym_dir, f)):
            res["fix"].append(f"缺 {label}")

    try:
        s = scan(elmt)
    except ET.ParseError as e:
        res["fix"].append(f"XML 解析失败: {e}")
        return res
    root, info_text = s["root"], s["info"]

    defs = list(root.iter("definition"))
    if not defs:
        res["fix"].append("无 <definition>")
        return res
    d0 = defs[0]
    try:
        W = float(d0.get("width") or 0)
        H = float(d0.get("height") or 0)
    except ValueError:
        res["fix"].append("width/height 非数值")
        return res
    res["size"] = f"{W:g}x{H:g}"

    if W <= 0 or H <= 0:
        res["fix"].append("width/height 为 0")
    if W > OVERSIZE_UNITS or H > OVERSIZE_UNITS:
        res["check"].append(f"尺寸 {W:g}x{H:g} 单位（={W*0.254:.0f}x{H*0.254:.0f} mm）超出 {OVERSIZE_UNITS} 单位，图面是否失控")

    # 坐标制式 + filling 白名单
    bad_coord, bad_fill = [], []
    n_line = n_circle = n_rect = n_term = 0
    black_dots = []
    widths = set()
    for el in root.iter():
        tag = el.tag
        if tag == "line":
            n_line += 1
        elif tag == "circle":
            n_circle += 1
        elif tag == "rect":
            n_rect += 1
        elif tag == "terminal":
            n_term += 1
        if tag not in ("line", "rect", "circle", "arc", "polygon", "polyline", "terminal"):
            continue
        for a in ("x", "y", "x1", "y1", "x2", "y2"):
            v = el.get(a)
            if v is None:
                continue
            try:
                fv = float(v)
            except ValueError:
                bad_coord.append(f"{tag}.{a}={v}")
                continue
            if not half_grid_ok(fv):
                bad_coord.append(f"{tag}.{a}={v}")
        if tag in ("line", "rect", "arc", "circle", "polygon", "polyline"):
            w = el.get("line_width") or el.get("width")
            if w and tag != "rect":
                widths.add(w)
        fl = el.get("filling")
        if fl is not None and fl.lower() not in ALLOWED_FILLING:
            bad_fill.append(f"{tag}.filling={fl}")
        if fl == "full":
            res["fix"].append("filling=full 一票拦截（QET 只认 none/black/white）")
        if tag == "circle" and (fl or "").lower() == "black":
            try:
                black_dots.append(float(el.get("diameter")))
            except (TypeError, ValueError):
                pass
    if bad_coord:
        res["fix"].append(f"非半格坐标 {len(bad_coord)} 处：{', '.join(bad_coord[:3])}")
    if bad_fill:
        res["fix"].append(f"非法 filling {len(bad_fill)} 处：{', '.join(bad_fill[:3])}")

    # 单位标定：作废表述
    for pat in STALE_UNIT_PATTERNS:
        if re.search(pat, info_text):
            res["fix"].append("informations 含作废标定“1 格 = 34 单位”，应改 20 单位/格（1 单位 = 0.254 mm）")
            break

    # 元数据字段
    for field, pat in (
        ("条款号", r"\d{2}-\d{2}-\d{2}"),
        ("页码", r"PDF\s*页?\s*[：:]?\s*\d+|第\s*\d+\s*页|印刷页"),
        ("PDF SHA", r"[0-9a-f]{64}"),
        ("作者", r"作者"),
        ("日期", r"20\d{2}-\d{2}-\d{2}"),
    ):
        if not re.search(pat, info_text):
            res["check"].append(f"informations 缺{field}")

    # 端口
    if n_term == 0:
        res["fix"].append("无 terminal 端口，图上看不出接线点")
    # 连接点比例
    for dia in black_dots:
        r = dia / W if W else 0
        if not (DOT_RATIO_RANGE[0] <= r <= DOT_RATIO_RANGE[1]):
            res["check"].append(f"实心点直径 {dia:g} 单位（={dia*0.254:.2f} mm）= 框宽的 {r:.2f}，偏离标准页 0.13–0.16，图面上会显得过粗/过细")
            break

    # hotspot 落在框内（两种写法：<hotspot x= y=> 子元素，或 definition 的 hotspot_x/hotspot_y 属性）
    hx = hy = None
    hs = root.find(".//hotspot")
    if hs is not None:
        try:
            hx, hy = float(hs.get("x")), float(hs.get("y"))
        except (TypeError, ValueError):
            res["check"].append("hotspot 非数值")
    elif d0.get("hotspot_x") is not None and d0.get("hotspot_y") is not None:
        try:
            hx, hy = float(d0.get("hotspot_x")), float(d0.get("hotspot_y"))
        except (TypeError, ValueError):
            res["check"].append("hotspot_x/y 非数值")
    else:
        res["check"].append("无 hotspot")
    if hx is not None and hy is not None and not (-1 <= hx <= W + 1 and -1 <= hy <= H + 1):
        res["check"].append(f"hotspot ({hx:g},{hy:g}) 在外框外")

    res.update(lines=n_line, circles=n_circle, rects=n_rect, terms=n_term,
               line_widths=sorted(widths))
    return res


def render_check(sym_dir: str, sym_id: str) -> str | None:
    """调 QET --check-elements；返回错误文本或 None。"""
    elmt = os.path.join(sym_dir, f"{sym_id}.elmt")
    if not os.path.exists(elmt) or not os.path.exists(QET):
        return None
    env = dict(os.environ, DISPLAY=os.environ.get("DISPLAY", ":236"), QT_QPA_PLATFORM="xcb")
    env.pop("LD_PRELOAD", None)
    try:
        p = subprocess.run([QET, "--check-elements", elmt], capture_output=True,
                           text=True, env=env, timeout=120)
    except Exception as e:  # noqa: BLE001
        return f"QET 调用失败: {e}"
    out = "\n".join(l for l in (p.stdout + p.stderr).splitlines() if "proxychains" not in l)
    if p.returncode != 0:
        return f"QET --check-elements rc={p.returncode}: {out[-300:]}"
    if re.search(r"error|failed|invalid", out, re.I):
        return f"QET 报告问题: {out[-300:]}"
    return None


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    do_render = "--render" in sys.argv
    targets = []
    for std_dir in sorted(os.listdir(SYMBOLS)):
        full = os.path.join(SYMBOLS, std_dir)
        if not os.path.isdir(full):
            continue
        for sym_id in sorted(os.listdir(full)):
            sd = os.path.join(full, sym_id)
            if not os.path.isdir(sd):
                continue
            if args and sym_id not in args and std_dir not in args:
                continue
            targets.append((std_dir, sym_id, sd))

    rows = []
    counts = {"PASS": 0, "FIX": 0, "CHECK": 0}
    for std_dir, sym_id, sd in targets:
        r = check_symbol(sd, sym_id)
        if do_render:
            err = render_check(sd, sym_id)
            if err:
                r["fix"].append(err)
        verdict = "FIX" if r["fix"] else ("CHECK" if r["check"] else "PASS")
        counts[verdict] += 1
        r["verdict"] = verdict
        r["std"] = std_dir
        rows.append(r)
        if verdict != "PASS":
            print(f"[{verdict}] {sym_id}: " + "; ".join(r["fix"] + r["check"]))

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("# 审核队列（tools/review_gate.py 自动生成）\n\n")
        f.write("机械项结论，不等于“已核对”。PASS 只代表可以进人工对照；\n")
        f.write("人工对照（标准 PDF 页逐项 + QET 渲染目视）通过后才可上传。\n\n")
        f.write(f"合计 {len(rows)} 件：PASS {counts['PASS']} / CHECK {counts['CHECK']} / FIX {counts['FIX']}\n\n")
        f.write("| 件 | 标准册 | 尺寸(单位) | 线/圆/方/端口 | 判定 | 问题 |\n")
        f.write("|---|---|---|---|---|---|\n")
        for r in rows:
            issues = "; ".join(r["fix"] + r["check"]) or "—"
            geom = f"{r.get('lines', '-')}/{r.get('circles', '-')}/{r.get('rects', '-')}/{r.get('terms', '-')}"
            f.write(f"| {r['id']} | {r['std'].replace('GB-T-','')} | {r.get('size','?')} | {geom} | {r['verdict']} | {issues} |\n")
    print(f"\n{len(rows)} 件：PASS {counts['PASS']} / CHECK {counts['CHECK']} / FIX {counts['FIX']} -> {OUT_MD}")
    return 0 if counts["FIX"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
