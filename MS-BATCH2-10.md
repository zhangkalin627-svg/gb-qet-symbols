# Master/slave 第 2 批 10 件（2026-11-24）

国标电气符号 QET 主从改型第 2 批：试点对 2 件＋新转 8 件。基线 6715713（第 1 批已推）。

本批 10 件：

- 试点对（原样采用，试点已在 QET 0.90 验证通过）：S00305（master/coil）、S00284（slave/NO/1/power）
- Master（type=coil）：S00316、S00317、S00318、S00319、S00323、S00324
- Slave：S00230（SW/1/simple）、S00231（SW/1/simple，转换触点按 QET 自带 contnonc.elmt 取 SW）

改动：每件只改 link_type 属性与 kindInformations 内容，几何、端子、UUID、dynamic_text 标签全不动；逐件验过 XML 解析、描述块字节一致、渲染 0 像素差别。function=generic 按试点结论删除，不加 `<input tagg="label">`。

注：13 个 master 至此全部完成；28 个 slave 已完成 7 件（S00227–S00231、S00235、S00284），余 21 件。待定 10 件（S00307–S00310、S00325/S00326、S00351、S00287、S00377/S00379）未动。
