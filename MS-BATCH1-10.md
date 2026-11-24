# Master/slave 第 1 批 10 件（2026-11-24）

国标电气符号 QET 主从改型第 1 批：6 个线圈转 master、4 个触点转 slave。基线 fda4588（590 件）。

试点：S00305（线圈→master）＋S00284（触点→slave）在 QET 0.90 实测通过——交叉引用挂在现有 dynamic_text 标签上，无需加 `<input tagg="label">`；function=generic 删除；BOM 只计 -K1 一件；保存→退出→重开链接仍在。

本批 10 件：

- Master（type=coil）：S00306、S00311、S00312、S00313、S00314、S00315
- Slave：S00227（NO/1/simple）、S00228（NO/1/simple）、S00229（NC/1/simple）、S00235（NC/2/simple）

改动：每件只改 link_type 属性与 kindInformations 内容，几何、端子、UUID、dynamic_text 标签全不动；逐件验过 XML 解析、描述块字节一致、渲染 0 像素差别。

注：S00306 与 S00228 在 informations 里标已废止/仅供参考，按改型清单仍在首批。试点对 S00305/S00284 已验证通过，本批未含它俩（41 件清单中共 13 master＋28 slave，首批 10 件后余 31 件，试点对 2 件计入后续批次）。
