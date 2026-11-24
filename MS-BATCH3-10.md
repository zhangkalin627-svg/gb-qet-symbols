# Master/slave 第 3 批 10 件（2026-11-24）

国标电气符号 QET 主从改型第 3 批：10 个触点转 slave。基线 dfad796（第 2 批已推）。

本批 10 件（§3.2 顺序，顺延）：

- Slave：S00232（SW/1/simple）、S00233（SW/1/simple）、S00234（NO/2/simple）、S00236（NO/1/simple）、S00237（NO/1/simple）、S00238（NO/1/simple）、S00239（NO/1/simple）、S00240（NO/1/simple）、S00241（NC/1/simple）、S00242（NC/1/simple）

改动：每件只改 link_type 属性与 kindInformations 内容，几何、端子、UUID、dynamic_text 标签全不动；逐件验过 XML 解析、描述块字节一致、渲染 0 像素差别。function=generic 按试点结论删除，不加 `<input tagg="label">`。

注：S00236–S00242 为过渡／先合／后断类触点，其时序语义 QET kind info 无法表达（图形本身承载含义，交叉引用中按普通 NO/NC 显示），为改型前已知限制，非本次引入。28 个 slave 已完成 17 件，余 11 件（S00243–S00252 共 10 件＋主触点 S00286 1 件）。待定 10 件未动。
