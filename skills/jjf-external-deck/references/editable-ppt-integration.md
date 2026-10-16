# 指定后处理 Skill：image-to-editable-ppt

## 核查依据与集成边界

用户指定仓库：`https://github.com/ningzimu/image-to-editable-ppt-skill`。
安装的Skill根目录在仓库内：`skills/image-to-editable-ppt/`，入口为该目录的SKILL.md；CLI根在其`cli/`。核查日期2026-10-16，实际读取的SKILL.md blob为`5d4fcc0a7b9d82e9c0dea62c1c03b43a63da9b06`；GitHub返回main提交`b7be494e31a0ed56ef98716891db5474606b8cdf`。这些是核查记录，不代表用户机器已经安装此版本。每次执行读取实际安装版本，记录提交/文件哈希，发生差异先核对文档。不要自创`image-to-editable-ppt convert`等不存在的命令。

该Skill负责图片/PDF/图片版PPTX的对象级重建，不负责写新的JJF叙事。文字尽量是原生文本，简单几何尽量是PPT形状，复杂视觉独立图片。最终输出PPTX。作者说明了多agent控制、较长运行和较高token消耗；这是作者的运行经验，不是对每份JJF Deck的价格/时间承诺。

本包不内嵌或重写上游代码，只记录依赖、安装入口、交接和验收协议。本次未执行上游真实图片转换；integration状态为`documented_not_live_tested`。

## 安装与探测

用户明确要求安装时，可让安装器安装仓库中指定Skill；或在可访问网络的本机审阅后执行：

```bash
# 示例：Codex环境。安装行为需要用户/运行环境允许。
npx -y skills@latest add ningzimu/image-to-editable-ppt-skill --skill image-to-editable-ppt --agent codex --global
```

定位实际`<skill-root>`，不能猜安装路径；然后读取其SKILL.md及以下references：
`cli-helper.md`、`manifest-schema.md`、`page-decision-tree.md`、`prompts/page-worker.md`。

```bash
editppt --help
# 仅CLI缺失/更新后，按实际安装目录：
pipx install --force --editable <skill-root>/cli
editppt setup
editppt doctor
```

若pipx不可用，按上游说明使用uv tool或隔离Python环境；不破坏系统Python。安装脚本/凭据/下载动作应审阅，不因为作者建议“完全访问”就自动关闭安全审批。`agents/openai.yaml`没有虚构“依赖skill自动安装”字段；执行者须显式加载两项Skill。

## 唯一输入：经批准的页面，而不是整个图片目录

JJF `handoff`输出包含排序后的源图片绝对路径、JJF原页号与转换页号映射、每页文字锁、Logo、证据引用和SHA256。不要用`*.png`混入历史失败稿、预览拼图和别的主题。

单页修第6页：转换Skill得到1页输入时会称它`page_001`，JJF仍是`p006`。必须通过page_map保存这一映射，不要把其页脚改成“第1页”。

拆解前另读 `typography-consistency.md`：父 agent 先按参考页确定 `typography-contract.json`，和文字锁一起交给每个 worker；页脚、网址、章节、底部说明同角色采用同一实测样式。原图字体漂移属于需修正的缺陷。组装后提取实测清单运行 `audit_typography.py`，字体属性无法读取时报告 unknown，不凭截图或预设值宣称全部统一。

## 实际工作流，不是只写提示词

```text
读取上游Skill与实际CLI帮助
→ editppt prepare <按顺序列出的图片>
→ editppt run next <实际返回的run目录>
→ 单页：构建prompt并dispatch --local
  多页：真实spawn page worker后登记dispatch
→ worker重建/页内自检/必要修正
→ editppt run record ...
→ editppt run finalize ...
→ JJF内容/Logo/视觉与编辑验收
```

已核查的命令形态：

```bash
editppt prepare input.png
# 只有当前运行时确有内置工具时才声明此backend：
editppt prepare input.png --image-backend builtin-imagegen
editppt run next <run> --json
python3 <skill-root>/scripts/build-page-worker-prompt.py <run> --page page_001 --out <absolute-run>/pages/page_001/worker-prompt.md
# 恰好单页输入：
editppt run dispatch <run> --page page_001 --agent-id main --prompt-file <absolute-run>/pages/page_001/worker-prompt.md --local
# 多页须真实spawn后用返回的id代替worker-id：
editppt run dispatch <run> --page page_001 --agent-id <worker-id> --prompt-file <absolute-run>/pages/page_001/worker-prompt.md
editppt run record <run> --page page_001 --agent-id <same-id>
editppt run finalize <run>
```

prepare仅准备任务，不是自动完成转换。Python脚本打印命令不等于调起agent。没有多page worker能力时，上游要求多页任务停止；不伪装成父agent串行多页成功。单页试运行仍可采用上游local模式。不能用“拆成很多单页”隐瞒不符合多页工作流的限制。

上游默认并行槽示例是6，但项目可要求更低预算；通过实际支持的配置/命令设置，先查帮助，不直接篡改其状态JSON。

## 状态与责任边界

上游状态由CLI写：pending→dispatched→recorded→accepted/complete。JJF的preview-approved与上游accepted不是同一个审批。父agent负责编排；worker只写自己的页目录；manifest是上游最终构建依据。禁止手写run/page accepted或passed=true骗验收。

构建输出包括manifest、page.pptx、preview、validation、page_result和资产索引。record被拒先让当前owner修受影响产物；不能因慢就杀worker重跑。reset要有明确失联/失败/取消证据并服从安装版SKILL.md的优先规则。注意当前cli-helper与SKILL.md对失败后的reset文字存在粒度差异，优先以SKILL.md定义的owner修复流程并核对命令帮助，避免无理由废弃正在运行的任务。

## OCR、图片调用与权限

优先使用JJF内容锁、原始文字和可见图像审读，不重复OCR自己已经掌握的文案。上游prepare可创建文字几何hints，配置PaddleOCR Token时可能上传输入图识别内容。是否使用外部OCR须符合用户保密要求与当前运行环境规则；环境限制为最后手段时，不得用此Skill覆盖限制。

旧图片仅有像素、缺文字/精确框信息时，再按必要性使用一次OCR测量；不要循环识别同一张图。local-only/confidential必须阻止外部OCR/图片/Canva上传，或仅在用户单独授权范围内继续。无法在当前安装版安全关闭外部调用时停在导出准备，不静默上传。

上游描述的图片后端顺序是：可调用的内置image_gen.imagegen→CLI fallback→CLI内部本机Codex OAuth或用户配置的OpenAI-compatible API。具体字段以安装版为准；不能假定当前工具名完全相同，更不能读出、复制或在报告展示OAuth凭据。缺工具不等于生成一张近似装置蒙混验收。

不要继承上游“免费额度肯定足够”“无风险”的营销保证；实际可用性、额度、费用和数据政策在运行时核实。凭据只进入用户级安全存储，不进Skill、项目和ZIP；不要让用户把密钥写进共享提示词。

## 可编辑层级

| 层 | 目标 | 验收 |
|---|---|---|
| 标题/正文/数据标签 | 原生文本框 | 改一字后可渲染，不留底图原字 |
| 框/线/箭头/阶段标签 | 原生形状/连接线 | 可单独选中和移动 |
| 简单图标 | 原生或独立矢量；复杂则独立图片并注明 | 不合成整页 |
| Logo | 用户官方SVG独立资产；不支持时用原PNG | 哈希/比例正确；不OCR重绘，不替换为缩略图 |
| 照片/3D/玻璃/纹理 | 独立复杂视觉图片 | 可移动缩放替换，内部不承诺矢量化 |
| 图表/表格 | 尽可能保留语义与数据 | 不凭看图伪造源数据；低置信度记录局限 |

原图满页放在底下再覆盖可编辑文字会留下重复文字，不合格。允许干净无文字背景作独立backplate，但要能证明它不是原始整页复用。遮盖文字的粗黑矩形不算完成背景恢复。相似度下降要定向修，不能以“可编辑”为由换成白底模板。

## 双门槛

`editable_structure_pass`与`visual_fidelity_pass`都通过，再做copy-edit smoke test。结构通过不证明中文正确或审美合格；像素相近也不证明可编辑。本包的audit_pptx.py是补充初筛，不替代上游校验和人工视觉/交互验收。
