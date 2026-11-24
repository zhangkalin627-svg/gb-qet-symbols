# Master/slave 第 5 批 1 件（2026-11-24）

国标电气符号 QET 主从改型第 5 批：最后 1 件。基线 85a54a5（第 4 批已推）。

本批 1 件：

- Slave：S00286（NC/1/power，接触器的主动断触点，07-13-04；与试点从件 S00284 同族，彼为 NO/1/power）

改动：只改 link_type 属性与 kindInformations 内容，几何、端子、UUID、dynamic_text 标签全不动；验过 XML 解析、描述块字节一致、渲染 0 像素差别。function=generic 按试点结论删除，不加 `<input tagg="label">`。

至此 41 件可转项全部完成（13 master＋28 slave）。待定 10 件（S00307–S00310、S00325/S00326、S00351、S00287、S00377/S00379）未动，等裁定。
