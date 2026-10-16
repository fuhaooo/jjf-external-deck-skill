---
name: jjf-external-deck
description: Use when creating or revising JJF AI Craft Labs external decks, OPC ecosystem proposals, FDE or AI training introductions, developer-community and global-event presentations, or preparing those JJF slides for editable PowerPoint or Canva. Also use when JJF slides drift in topic, branding, visual rhythm, or final-version selection.
---
# JJF External Deck

把 JJF 的真实能力组织成可理解、可验证、可复用的对外叙事。品牌统一不等于每页套同一个模板；图片好看不等于已交付可编辑 PPT。

## 先读取

- 每次：`references/brand-and-visual-system.md`、`references/workflow.md`。
- 本会话复盘：`references/session-retrospective.md`；不要把失败图当正例。
- OPC 新项目：`references/opc-storyboard.md`、`templates/opc19-content-lock.json`。
- 其他 JJF 介绍：`references/narrative-and-evidence.md`、`references/narrative-presets.md`；不强制套 OPC 19 页。
- 定稿转可编辑：`references/editable-ppt-integration.md`。
- 拆解、组装及跨页标签修订：`references/typography-consistency.md`；先建立同角色文字合同，不能照抄 AI 原图的字体漂移。
- Canva：`references/canva-handoff.md`。
- 修改已有 Canva：另读 `references/canva-in-place-editing.md`；已有原生对象直接局部编辑，不重走生成/拆解。
- 验收：`references/qa-and-release.md`；工具：`scripts/deckctl.py --help`。

## 不可突破

1. 正式 Logo 默认用 `assets/logo/jjf-logo-primary.svg`，不支持 SVG 时用兼容的 `jjf-logo-master.png`。其他官方变体及用途见 `assets/logo/README.md`。禁止 AI 重绘、替换成普通 JJF 字母或从旧图裁出错误 Logo；全套采用同一已选版本，保留比例、透明度及原有阴影。
2. 区分业务原始材料、已锁叙事、视觉参考。投标书是证据，不自动接管页序；“重做第 6 页”仍是双引擎，不是空间规划。
3. 只调整视觉时，保留页号、主题、主结论和必备内容；压缩文案不能删掉经营逻辑。内容改动另记 revision，使受影响页的旧审批失效；未变页保留。用户已授权自动纠错/自行验收时沿用授权，记录依据，不逐项重复确认，也不冒称用户逐页批准。
4. 默认深色黑绿系统。用构图、尺度、主视觉和信息密度变化避免疲劳；不要擅自变成白米色地产宣传册。没有人物不等于每页都用玻璃球、绿环或发光立方体。
5. 每页一个主视觉、一个主结论。文字越多，背景越安静。没有可靠来源的数据、案例身份、合作 Logo 或政策权益不进入正式宣传稿。
6. 主办、协办、参赛、出席、导师分别记录。自述、已核事实、计划、示例、待确认、冲突口径分开。生成的活动/人物/办公室图不能证明 JJF 办过活动或拥有该空间。
7. 每页只交付一个明确的当前候选/定稿。失败稿留内部。工具自动展示后不再以另一种“分析输出”重复发不同稿。图片下载链接与预览必须对应相同文件哈希。
8. 不凭“最新文件名”、继续生成下一页或没有异议认定全部已获用户批准。记录具体审批证据；获授权自主设计时可由设计负责人验收，但不得写成用户批准。
9. PNG 是预览；原生文本/图形加独立复杂视觉资产才是混合可编辑交付。禁止整页原图＋透明文字冒充可编辑。
10. 不在本项目里自动安装远程代码、泄露素材、公开上传私有图片、关闭安全审批或突破预算。缺少生图/子 agent/OCR/网络能力时如实标记阻塞，不编造调用或成功。

## 执行

**A 接收与锁定**：读需求和附件；已有明确 brief 时直接继续。记录受众、场景、语言、页数、预算、输出路径和保密边界。建立 `content-lock.json`、`deck.manifest.json`、证据台账。新整套先确认叙事与少量代表页；明确的单页修改不反复询问同一问题。

**B 设计导演**：给每页选择视觉家族与密度，检查前后两页。使用 `prompts/page-generation.md` 或 `prompts/page-revision.md`。固定 Logo、配色、字体层级、页脚；变化构图和视觉隐喻。正例只取对应价值，不复制旧图中的数据和 Logo。

**C 生成与改稿**：探测当前工具真实能力。优先生成不带文字/Logo的主视觉并独立排版；已有整页图片走图片优先路线。工具自动显示失败图时立刻指出无效，只修当前页，不同时创建另一套稿。所有输出使用明确返回路径，登记 revision、源图哈希、文字版本、视觉家族及结果。

**D 图片验收**：核对内容锁、Logo、中文、可读性、视觉焦点、相邻页差异；正确后才能展示/批准。阶段仅为 `preview-approved`，不宣称可编辑完成。

**E 工程收尾**：对批准的整页图片，必须读取并实际调用用户指定 `$image-to-editable-ppt`；按其安装版本的状态机执行，不能只写一句提示词代替运行。先锁定页码、章节、网址、底部说明等语义角色的中英文字体、字号/字重、字距/行距及锚点，把同一合同交给所有 workers；组装后按角色横向验收，不保留 AI 生图的字体缺陷。先做代表页试转换，再批量。已有原生层可直接组装，不为形式而栅格化再 OCR；记录 `native-direct` 与跳过图片转换的依据。具体命令与边界见集成规范。

**F 最终交付**：检查原生文本、独立资产、来源、PPTX结构、渲染与实际编辑；新制 Deck 默认导入新的 Canva 设计。用户明确要求修改指定原设计时，按局部编辑规范备份、编辑、保存及回读原设计。返回最终文件/原设计链接、明确的可编辑边界、验收结果及未完成项；不显示调试过程充当设计成品。

## 快捷调用

`$jjf-external-deck 重新设计第6页，只改视觉，保持双引擎内容与黑绿体系。`

`$jjf-external-deck 基于这些真实材料制作政府/园区合作版，先确认叙事和3张代表页，再生成并转换为可编辑PPT。`

`$jjf-external-deck 将已批准图片执行image-to-editable-ppt，验收后放入一个新的Canva设计。`
