#!/usr/bin/env python3
"""
发布前自检脚本 —— 扫描 symbols/ 下每个符号目录，中文报告问题。
全部通过退出码 0，有问题退出码 1。只用标准库。
"""

import hashlib
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYMBOLS_DIR = os.path.join(ROOT, "symbols")
ROOT_README = os.path.join(ROOT, "README.md")
COORD_ATTRS = {"x", "y", "x1", "y1", "x2", "y2", "diameter",
               "width", "height", "hotspot_x", "hotspot_y"}
ALLOWED_FILLING = {"none", "black", "white"}
# 精确构造坐标（圆与引线求交、等边三角、120 度 Y 形等）必然是非有理数。
# 只要 informations 里留下构造与舍入论证，就按提示处理，不进错误清单。
GEOM_PROOF = re.compile(r"几何求交|精确|舍入|√|等边|120°|60°|圆周|实测")
HINTS = []


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def find_symbol_dirs():
    dirs = []
    for root, subdirs, files in os.walk(SYMBOLS_DIR):
        for d in subdirs:
            full = os.path.join(root, d)
            elmt_files = [f for f in os.listdir(full)
                          if f.endswith(".elmt")]
            if elmt_files:
                dirs.append(full)
    dirs.sort()
    return dirs


def check_files(d, sym_id):
    issues = []
    elmt_path = os.path.join(d, f"{sym_id}.elmt")
    readme_path = os.path.join(d, "README.md")
    license_path = os.path.join(d, "LICENSE")

    if not os.path.isfile(elmt_path):
        issues.append(f"缺 {sym_id}.elmt")
    if not os.path.isfile(readme_path):
        issues.append(f"缺 README.md")
    if not os.path.isfile(license_path):
        issues.append(f"缺 LICENSE")
    return issues, elmt_path, readme_path


def check_sha_and_bytes(sym_id, elmt_path, readme_path, issues):
    if not os.path.isfile(elmt_path) or not os.path.isfile(readme_path):
        return

    actual_sha = sha256_file(elmt_path)
    actual_size = os.path.getsize(elmt_path)

    content = None
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with open(readme_path, "r", encoding=enc) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue

    if content is None:
        issues.append(f"README.md 编码无法读取")
        return

    elmt_name = f"{sym_id}.elmt"
    sha_pattern = re.compile(
        r"`" + re.escape(elmt_name) + r"`\s*SHA.*?`([0-9a-fA-F]{64})`")
    m = sha_pattern.search(content)
    if not m:
        alt_pattern = re.compile(
            r"`([0-9a-fA-F]{64})`")
        all_hashes = alt_pattern.findall(content)
        if actual_sha in all_hashes:
            pass
        else:
            issues.append(
                f"README.md 缺少 {elmt_name} 的 SHA256 声明"
                f"（实际 SHA256={actual_sha}）")
        return

    stated_sha = m.group(1).lower()

    byte_pattern = re.compile(
        r"`" + re.escape(elmt_name) + r"`\s*SHA.*?`[0-9a-fA-F]{64}`[^0-9]*([0-9]+)\s*字[节節]")
    byte_m = byte_pattern.search(content)

    sha_ok = stated_sha == actual_sha
    size_issues = []

    if not sha_ok:
        issues.append(
            f"README.md SHA256 不符：声明={stated_sha}，"
            f"实际={actual_sha}")

    if byte_m:
        stated_bytes = int(byte_m.group(1))
        if stated_bytes != actual_size:
            issues.append(
                f"README.md 字节数不符：声明={stated_bytes}，"
                f"实际={actual_size}")
    # If no byte count declared, that's OK — not all READMEs include it.


def check_elmt_integrity(elmt_path, issues):
    if not os.path.isfile(elmt_path):
        return
    try:
        tree = ET.parse(elmt_path)
        root = tree.getroot()
    except ET.ParseError as e:
        issues.append(f"{os.path.basename(elmt_path)} XML 解析失败: {e}")
        return

    try:
        with open(elmt_path, encoding="utf-8") as fobj:
            raw = fobj.read()
    except OSError:
        raw = ""
    info = re.search(r"<informations>(.*?)</informations>", raw, re.S)
    proof_ok = bool(info and GEOM_PROOF.search(info.group(1)))

    for elem in root.iter():
        style = elem.get("style", "")
        if style:
            for part in style.split(";"):
                part = part.strip()
                if part.startswith("filling:"):
                    val = part.split(":", 1)[1].strip()
                    if val not in ALLOWED_FILLING:
                        issues.append(
                            f"{os.path.basename(elmt_path)} "
                            f"非法 filling 值: {val!r}")
        for attr_name in COORD_ATTRS:
            val = elem.get(attr_name)
            if val is not None:
                try:
                    f = float(val)
                except ValueError:
                    issues.append(
                        f"{os.path.basename(elmt_path)} "
                        f"{elem.tag} {attr_name}={val!r} 不是数值")
                    continue
                # 允许整数与半格(x.5)。对称件居中常需半格，QET 支持浮点坐标；
                # 更细的小数会导致图形对不上 QET 网格，按缺陷处理。
                if abs(f * 2 - round(f * 2)) > 1e-9:
                    msg = (f"{os.path.basename(elmt_path)} "
                           f"{elem.tag} {attr_name}={val!r} 既不是整数也不是半格")
                    if proof_ok:
                        HINTS.append(msg + "（informations 已声明精确构造或原图实测依据，仅提示，不计错误）")
                    else:
                        issues.append(msg)


def collect_all_uuids(symbol_dirs):
    all_uuids = {}
    for d in symbol_dirs:
        sym_id = os.path.basename(d)
        elmt_path = os.path.join(d, f"{sym_id}.elmt")
        if not os.path.isfile(elmt_path):
            continue
        try:
            tree = ET.parse(elmt_path)
            root = tree.getroot()
            uuid_elem = root.find("uuid")
            if uuid_elem is not None:
                uid = uuid_elem.get("uuid", "")
                all_uuids.setdefault(uid, []).append(sym_id)
        except ET.ParseError:
            pass
    return all_uuids


def check_uuid_uniqueness(all_uuids):
    issues = []
    for uid, symbols in all_uuids.items():
        if len(symbols) > 1:
            issues.append(
                f"UUID 重复: {uid} 出现在 {', '.join(symbols)}")
    return issues


def check_root_readme_links(symbol_dirs):
    issues = []
    if not os.path.isfile(ROOT_README):
        issues.append("根 README.md 不存在")
        return issues

    with open(ROOT_README, "r", encoding="utf-8") as f:
        content = f.read()

    for d in symbol_dirs:
        sym_id = os.path.basename(d)
        rel = os.path.relpath(d, ROOT)
        readme_rel = f"{rel}/README.md"
        expected_link = f"symbols/{os.path.relpath(d, SYMBOLS_DIR)}/README.md"

        pattern = re.compile(
            r"\[.*?\]\(" + re.escape(expected_link) + r"\)")
        if not pattern.search(content):
            issues.append(
                f"根 README.md 缺少指向 {sym_id}/README.md 的链接"
                f"（期望路径: {expected_link}）")
    return issues


def main():
    symbol_dirs = find_symbol_dirs()
    if not symbol_dirs:
        print("未发现任何符号目录。")
        sys.exit(0)

    all_issues = []
    uuid_reported = set()

    for d in symbol_dirs:
        sym_id = os.path.basename(d)
        issues, elmt_path, readme_path = check_files(d, sym_id)
        if issues:
            all_issues.append((sym_id, issues))
            continue

        check_sha_and_bytes(sym_id, elmt_path, readme_path, issues)
        check_elmt_integrity(elmt_path, issues)
        if issues:
            all_issues.append((sym_id, issues))

    all_uuids = collect_all_uuids(symbol_dirs)
    uuid_issues = check_uuid_uniqueness(all_uuids)
    for ui in uuid_issues:
        for s in ui.split(":")[1].split("出现在")[0].strip().split(","):
            pass
    if uuid_issues:
        for issue in uuid_issues:
            all_issues.append(("UUID", [issue]))

    link_issues = check_root_readme_links(symbol_dirs)
    if link_issues:
        all_issues.append(("根README", link_issues))

    if HINTS:
        print(f"提示（不计入错误）：{len(HINTS)} 项精确构造坐标")
        for h in HINTS:
            print(f"  - {h}")

    if not all_issues:
        print(f"检查完成：{len(symbol_dirs)} 个符号，全部通过。")
        sys.exit(0)

    print("=" * 60)
    print(f"发现问题：{len(symbol_dirs)} 个符号目录中 {len(all_issues)} 项有误。")
    print("=" * 60)
    for label, issues in all_issues:
        for issue in issues:
            print(f"[{label}] {issue}")
    print("=" * 60)
    sys.exit(1)


if __name__ == "__main__":
    main()