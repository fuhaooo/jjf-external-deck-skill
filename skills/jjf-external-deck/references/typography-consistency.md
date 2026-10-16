# 拆解后的跨页文字一致性

原图是内容和构图依据，不是所有字体差异的规范。AI 生图会把同一网址、页码、章节名画成不同字体；拆解必须主动消除这些缺陷。不能只逐页“看起来像原图”，还要按语义角色横向验收全套。

## 先定角色，再定样式

至少盘点 `page_footer`（页码＋英文页名）、`website_footer`、`service_footer`（底部服务说明）、`chapter_eyebrow`（顶部章节标签）；同类卡片标题、步骤号等确有跨页重复的元素也建角色。Logo 品牌区仍按 header_lockup 单独管理。

以用户指定页为第一参考；没有明确参考时选可读、完整的代表页，形成项目 `typography-contract.json`，不要每个 page worker 自行选字体。相同角色锁定中英文字体、视觉字号、字重、字距、行距、颜色、对齐和锚点。页名长度不同时可以保留不同框宽；右对齐网址则固定右边界和框宽。不要为一行长文案逐页缩字号，先检查框宽和不必要的空格。

参考 `templates/typography-contract.json`，其中数值只是生产起点，必须按项目参考更新；填写实际目标页 ID 的 `expected_pages`，删除不适用角色。封面 CTA、封面较大网址或内文不同层级可以独立建 `cover_website` 等角色并记录理由；没有顶部章节的页不强加章节。用户明确覆盖项优先，不能借一致性重写文案或把全套标题/正文压成同一字号。全套字体 fallback 必须统一、真实可用并记录，不能每页随机替换。

## 在拆解与组装时落实

父 agent 把同一合同传给所有 page workers；worker 用合同重建这些原生文本，而不是照抄每张图的缺陷。内容仍以文字锁为准。主 deck 组装后、导入 Canva 后各复查一次。输入图中错误文字须从独立背景清理，不能以叠两层字或遮盖粗黑块冒充完成。

仅修改指定范围：保存改前对象、元素 ID 和角色映射；每个目标页做局部格式/几何修正，再检查非目标对象和页序。无需重新生成已经合格的页面。重复角色缺失、同页重复对象和不同字体均是明确差异，不因总体缩略图好看而忽略。

## 实测清单与机械检查

把平台回读、PPTX 对象属性或有据可查的实测写入项目 `typography-inventory.json`。每项一个原生文本对象，包含 `page_id`、`element_id`、`role`、实际读回的 `text`、`native_text`、`source`、`canvas_px`、`style` 和 `box`。`source` 写提取途径/证据文件，不含凭据或临时签名 URL。仅填写真实已读取的属性；主题/母版继承未解析、平台没有提供字体时用 null，不从合同倒填期望值。一个语言脚本内部有多个字体时先拆分角色或报告混合值，不能只取第一个字体代表全部。

颜色也是必测字段；合同漏掉颜色不能跳过验收。实际 `text` 含中文、日文或韩文字形时，合同和观测必须都提供 `font_family_cjk`；纯英文网址不强加 CJK 字体。缺少实际文字无法判断脚本覆盖，报告 unknown。字号、行距倍率和框宽/高必须为正值，合同与观测同时填零或负数也属于无效输入。

示例是一份单元素的观测结构，字体未知会产生 unknown：

```json
{
  "schema_version": "1.0",
  "elements": [{
    "page_id": "p002", "element_id": "actual-object-id", "role": "page_footer",
    "text": "第二页 | Why OPC, Why Now",
    "native_text": true, "source": "saved-state.json plus native property inspector",
    "canvas_px": [1920, 1080],
    "style": {"font_family_latin": null, "font_family_cjk": null, "font_size_px": 22,
      "font_weight": "normal", "letter_spacing_px": 0, "line_height": 1.1,
      "text_align": "start", "color": "#FFFFFF"},
    "box": {"x": 48, "y": 1010, "width": 400, "height": 30}
  }]
}
```

```bash
python <skill-root>/scripts/audit_typography.py <project>/typography-contract.json <project>/typography-inventory.json --out <project>/typography-audit.json
```

仅使用 Python 标准库。退出码 0=已测字段和范围通过，1=差异/无效输入，2=未知属性/缺测。它检查同角色的字体、字号/字重/字距/行距/颜色/对齐、归一化几何、目标页覆盖及原生文本标记；未知属性绝不算通过。清单由调用者真实提取，本脚本不自动连接 Canva、不自动解析 PPTX 的母版继承，也不替代视觉和编辑实验。

几何和视觉字号均按各观测的 `canvas_px` 换算至合同坐标。PPTX 的 pt 应乘以“目标渲染高度 px ÷ 页面高度 pt”，不是一律乘 2；Canva 中带变换的字号也不能直接当渲染 px。平台只给字号但无法解析变换时标 unknown。字距用 px，行距用倍率，不混用磅/百分比。截图只可核对基线/视觉高度，不能可靠证明字体家族。

## Canva 能力与验收

先读当前工具 schema；部分编辑接口支持字号/字重但不支持字体家族、字距或按片段设置。遇到这类接口，不能声称调用 `format_text` 就已统一字体家族。优先用可用的原生文字属性编辑/检查入口；缺能力时明确记录已统一字段与未验证字段，保留原生文本。不得静默把页码、网址等普通文字转换成 SVG 轮廓或图片来取得外观一致。确需矢量替代时记录原因和逐字编辑限制，用户明确要求逐字编辑时不以此冒充完成。

保存后回读并逐页截图；全套并排检查重复标签的基线、尺寸、行距、对齐及文字换行，同时看邻近正文是否被挤压。需验证的两关是“同角色样式符合合同”和“保存后实际渲染协调、文字可编辑”。审计通过只能证明清单中的实测字段，不能自动升级为全套视觉或 Canva 编辑验收通过。
