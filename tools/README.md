# tools/

仓库工具脚本。

## gen_elmt.py —— 参数化 .elmt 生成器

输入 JSON 规格，输出合法 QET `.elmt` 文件。

```
python3 tools/gen_elmt.py spec.json -o output.elmt
python3 tools/gen_elmt.py -t               # 内置测试件
```

JSON 规格格式：
```json
{
  "width": 272, "height": 136,
  "hotspot_x": 136, "hotspot_y": 68,
  "names": {"zh": "中文名", "en": "English Name"},
  "informations": "描述信息",
  "uuid": "{可选-UUID}",
  "elements": [
    {"type": "line", "x1": 0, "y1": 68, "x2": 272, "y2": 68,
     "color": "black", "filling": "none", "antialias": "false"},
    {"type": "circle", "x": 119, "y": 34, "diameter": 34,
     "filling": "none"},
    {"type": "terminal", "x": 0, "y": 68, "orientation": "w"}
  ]
}
```

**实测坑：**

1. **椭圆 `<ellipse>` 不可用。** QET 0.100 会静默忽略 `description` 里的 `<ellipse>` 元素，`--check-elements` 仍报 OK 但 `--export-pdf` 后椭圆完全消失。因此本生成器不输出椭圆元素。
2. **椭圆用折线近似。** 提供 `ellipse_as_lines(cx, cy, rx, ry, n=48)` 辅助函数。S00009 用 48 段折线，经验证 PDF 导出渲染正常，肉眼无法分辨。
3. **`<circle>` 是可靠的。** 可正常使用，元素属性 `x`/`y` 是边界框左上角，`diameter` 是直径（不是半径）。
4. **coords 必须为整数。** 所有坐标属性必须是 Python `int` 类型，非整数直接抛 `TypeError`。
5. **filling 只允许 `none`/`black`/`white`。** 其他值直接抛 `ValueError`。
6. **color 只允许 `black`/`white`。**
7. **UUID 格式：** `{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}` 带花括号。

## check_release.py —— 发布前自检

扫描 `symbols/` 下所有符号目录，中文报告问题。

```
python3 tools/check_release.py
```

检查项：

| 检查项 | 说明 |
|--------|------|
| 必需文件 | 每个符号目录必须有 `<编号>.elmt`、`README.md`、`LICENSE` |
| SHA256 | README.md 里声明的 SHA256 必须等于 .elmt 文件实际 SHA256 |
| 字节数 | 如有声明字节数，必须等于 .elmt 实际文件大小 |
| filling 值 | 所有 filling 只能是 `none`/`black`/`white` |
| 坐标整数 | 所有坐标属性（x/y/x1/y1/x2/y2/diameter/width/height/hotspot_x/hotspot_y）必须是整数 |
| UUID 唯一 | 所有 .elmt 的 uuid 不可全局重复 |
| 根 README 索引 | 根 README.md 必须有指向每个符号目录 README.md 的链接 |