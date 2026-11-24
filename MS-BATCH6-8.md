# Master/slave 第 6 批 8 件（2026-11-24）

国标电气符号 QET 主从改型第 6 批：此前待定的 10 件中 8 件定性转主件，2 件留 simple。基线 52c82bc（第 5 批已推）。

本批 8 件：

- Master（type=coil）：S00307、S00308、S00309、S00310（双绕组驱动器件，一器件一标签一 BOM 项；QET 自带 4 端子线圈主件为证）、S00325（热继电器驱动器件；QET 自带 comm_thermique 为 master/coil）、S00326（电子继电器驱动器件；QET 自带 comm_electronique 为 master/coil）
- Master（type=protection）：S00351（过流继电器；保护主件族类比，暂定）、S00287（断路器；QET 自带 disjonct-m_1f 为 master/protection）

改动：每件只改 link_type 属性与 kindInformations 内容，几何、端子、UUID、dynamic_text 标签全不动；逐件验过 XML 解析、描述块字节一致、渲染 0 像素差别。function=generic 按试点结论删除，不加 `<input tagg="label">`。

暂定项：S00307–S00310（一标签管两绕组，验收时核对主件列表显示）与 S00351（无一对一自带过流继电器件，凭保护主件族＋功能定性，验收时核对主件列表显示）。

未转 2 件（有意留 simple，非遗漏）：S00377 静态接触器（无线圈、非保护、无换向功能，开关路径画在符内，无可归属的从件）；S00379 静态继电器（线圈＋半导体触点复合一符，内有虚线联线；主从是两元件间的关系，不在一符内部，同 S00320–S00322 例）。

至此 41 件可转项＋待定 10 件中的 8 件全部完成（49 件主从件）；S00377、S00379 保持 simple。
