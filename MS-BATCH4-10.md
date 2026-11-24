# Master/slave 第 4 批 10 件（2026-11-24）

国标电气符号 QET 主从改型第 4 批：10 个触点转 slave。基线 51c4450（第 3 批已推）。

本批 10 件（§3.2 顺序，顺延）：

- Slave：S00243（NO/1/delayOn）、S00244（NO/1/delayOff）、S00245（NC/1/delayOff）、S00246（NC/1/delayOn）、S00247（NO/1/delayOn）、S00248（NO/3/simple，触点组，6 端子）、S00249（NO/1/simple）、S00250（NO/1/simple）、S00251（NC/1/simple）、S00252（SW/1/simple）

改动：每件只改 link_type 属性与 kindInformations 内容，几何、端子、UUID、dynamic_text 标签全不动；逐件验过 XML 解析、描述块字节一致、渲染 0 像素差别。function=generic 按试点结论删除，不加 `<input tagg="label">`。定义 UUID 逐件复核无变化。

注：S00243–S00247 的 delayOn/delayOff 取值按 QET 自带延时件类比，未经官方源确认，暂定（S00247 的 delayOn 尤为暂定）；S00248 的 number=3 在主件列表中的显示待验收时抽查。28 个 slave 已完成 27 件，只剩主触点 S00286 1 件。待定 10 件未动。
