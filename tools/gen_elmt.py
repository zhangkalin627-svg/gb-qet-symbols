#!/usr/bin/env python3
"""
QET .elmt parameterized generator.

实测坑：QET 0.100 会静默忽略 description 里的 <ellipse> 元素，
--check-elements 仍报 OK 但 --export-pdf 后椭圆完全消失。
因此本生成器不输出椭圆；需要椭圆时用 ellipse_as_lines() 折线近似。
S00009 用 48 段折线近似椭圆，经验证 PDF 导出正常。
注意 <circle> 是可靠的，可以正常使用。
"""

import json
import math
import sys
import uuid
import xml.dom.minidom
import argparse

ALLOWED_FILLING = {"none", "black", "white"}
VALID_ORIENTATIONS = {"n", "s", "e", "w"}


def make_uuid():
    return "{" + str(uuid.uuid4()) + "}"


def _check_int(val, name):
    if not isinstance(val, int) or isinstance(val, bool):
        raise TypeError(f"{name} 必须为整数，收到: {val!r}")
    return val


def _check_color(val):
    if val not in {"black", "white"}:
        raise ValueError(f"color 只允许 black/white，收到: {val!r}")
    return val


def _check_filling(val):
    if val not in ALLOWED_FILLING:
        raise ValueError(f"filling 只允许 none/black/white，收到: {val!r}")
    return val


def ellipse_as_lines(cx, cy, rx, ry, n=48):
    """
    用 n 段折线近似椭圆（中心 (cx,cy)，半轴 rx/ry）。
    返回 [(x1,y1,x2,y2), ...] 线段列表（闭合多边形）。
    实测：48 段足以通过 PDF 导出渲染，肉眼看不出来。
    """
    _check_int(cx, "cx")
    _check_int(cy, "cy")
    _check_int(rx, "rx")
    _check_int(ry, "ry")
    _check_int(n, "n")
    if n < 3:
        raise ValueError(f"椭圆折线段数 n 必须 >= 3，收到: {n}")
    points = []
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        px = int(round(cx + rx * math.cos(angle)))
        py = int(round(cy + ry * math.sin(angle)))
        points.append((px, py))
    segments = []
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        segments.append((x1, y1, x2, y2))
    return segments


def _int_attrs(elem, attrs):
    """将 attrs 中的键转为整数写入 elem XML 属性。"""
    for k, v in attrs.items():
        elem.setAttribute(k, str(_check_int(v, k)))


def _generate_elmt(spec):
    """
    spec 字典：
      width, height, hotspot_x, hotspot_y        (整数)
      names: {zh: str, en: str}
      informations: str
      elements: [
        {type: "line", x1, y1, x2, y2, color, filling, antialias},
        {type: "circle", x, y, diameter, color, filling, antialias},
        {type: "terminal", x, y, orientation},
      ]
      uuid: str (可选，不提供则自动生成)
    """
    doc = xml.dom.minidom.Document()

    definition = doc.createElement("definition")
    _int_attrs(definition, {
        "width": spec["width"],
        "height": spec["height"],
        "hotspot_x": spec.get("hotspot_x", spec["width"] // 2),
        "hotspot_y": spec.get("hotspot_y", spec["height"] // 2),
    })
    definition.setAttribute("link_type", "simple")
    definition.setAttribute("version", "0.5")
    definition.setAttribute("type", "element")
    doc.appendChild(definition)

    uuid_elem = doc.createElement("uuid")
    uuid_elem.setAttribute("uuid", spec.get("uuid", make_uuid()))
    definition.appendChild(uuid_elem)

    names_elem = doc.createElement("names")
    names = spec.get("names", {})
    zh = names.get("zh", "")
    en = names.get("en", "")
    name_zh = doc.createElement("name")
    name_zh.setAttribute("lang", "zh")
    name_zh.appendChild(doc.createTextNode(zh))
    names_elem.appendChild(name_zh)
    name_en = doc.createElement("name")
    name_en.setAttribute("lang", "en")
    name_en.appendChild(doc.createTextNode(en))
    names_elem.appendChild(name_en)
    definition.appendChild(names_elem)

    info_elem = doc.createElement("informations")
    info_elem.appendChild(doc.createTextNode(spec.get("informations", "")))
    definition.appendChild(info_elem)

    desc_elem = doc.createElement("description")
    for el in spec.get("elements", []):
        typ = el.get("type", "")
        if typ == "line":
            elem = doc.createElement("line")
            _int_attrs(elem, {"x1": el["x1"], "y1": el["y1"],
                                "x2": el["x2"], "y2": el["y2"]})
            elem.setAttribute("end1", el.get("end1", "none"))
            elem.setAttribute("end2", el.get("end2", "none"))
            elem.setAttribute("length1", el.get("length1", "1.5"))
            elem.setAttribute("length2", el.get("length2", "1.5"))
            color = el.get("color", "black")
            _check_color(color)
            filling = el.get("filling", "none")
            _check_filling(filling)
            elem.setAttribute("style",
                f"line-style:normal;line-weight:normal;filling:{filling};color:{color}")
            elem.setAttribute("antialias", el.get("antialias", "false"))
            desc_elem.appendChild(elem)

        elif typ == "circle":
            elem = doc.createElement("circle")
            _int_attrs(elem, {"x": el["x"], "y": el["y"],
                                "diameter": el["diameter"]})
            color = el.get("color", "black")
            _check_color(color)
            filling = el.get("filling", "none")
            _check_filling(filling)
            elem.setAttribute("style",
                f"line-style:normal;line-weight:normal;filling:{filling};color:{color}")
            elem.setAttribute("antialias", el.get("antialias", "false"))
            desc_elem.appendChild(elem)

        elif typ == "terminal":
            elem = doc.createElement("terminal")
            _int_attrs(elem, {"x": el["x"], "y": el["y"]})
            orient = el.get("orientation", "e")
            if orient not in VALID_ORIENTATIONS:
                raise ValueError(
                    f"terminal orientation 必须是 n/s/e/w，收到: {orient!r}")
            elem.setAttribute("orientation", orient)
            desc_elem.appendChild(elem)

        else:
            raise ValueError(f"未知元素类型: {typ!r}")

    definition.appendChild(desc_elem)
    return doc


def to_xml_string(spec):
    doc = _generate_elmt(spec)
    return doc.toprettyxml(indent="    ", encoding=None)


def main():
    parser = argparse.ArgumentParser(description="参数化 QET .elmt 生成器")
    parser.add_argument("input", nargs="?", default="-",
                        help="输入 JSON 规格文件（默认从 stdin 读取）")
    parser.add_argument("-o", "--output", default=None,
                        help="输出 .elmt 路径（默认输出到 stdout）")
    parser.add_argument("-t", "--test", action="store_true",
                        help="使用内置测试件生成并输出")
    args = parser.parse_args()

    if args.test:
        spec = {
            "width": 272,
            "height": 136,
            "hotspot_x": 136,
            "hotspot_y": 68,
            "names": {"zh": "测试符号", "en": "Test Symbol"},
            "informations": "GB/T TEST | 测试件 | 2026-11-17",
            "elements": [
                {"type": "line", "x1": 0, "y1": 68, "x2": 272, "y2": 68},
                {"type": "circle", "x": 119, "y": 34, "diameter": 34, "filling": "none"},
                {"type": "terminal", "x": 0, "y": 68, "orientation": "w"},
                {"type": "terminal", "x": 272, "y": 68, "orientation": "e"},
            ],
        }
    else:
        with sys.stdin if args.input == "-" else open(args.input, "r") as f:
            spec = json.load(f)

    xml_str = to_xml_string(spec)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(xml_str)
    else:
        sys.stdout.write(xml_str)


if __name__ == "__main__":
    main()