# JJF External Deck Skill v1.0.1

面向JJF AI Craft Labs对外宣传：品牌介绍、OPC生态方案、企业FDE、AI培训、开发者社区、海外活动与合作Deck。入口`SKILL.md`；详细规范按需加载。

**状态**：本地Skill包已创建；脚本测试见`tests/verification-report.json`。指定转换器集成已经按实际文档编写，但未在本轮完成真实PPT转换或Canva导入。它不是无需工具即可运行的万能生图程序。

## 安装

本文件命令以当前工作目录为本 Skill 根目录为前提；从仓库根目录先进入 `skills/jjf-external-deck`。仓库级一键安装说明见顶层 README。

解压后将整个`jjf-external-deck`文件夹放入Codex项目的`.agents/skills/`或用户目录`~/.agents/skills/`。必须复制整目录，包括Logo、references和templates；只贴SKILL.md会丢掉品牌与工具文件。

可在解压目录运行（Python脚本只复制本地文件，不下载依赖、不覆盖已有版本）：

```bash
python scripts/install_local.py --scope user
# 或仅当前项目
python scripts/install_local.py --scope project --project /path/to/jjf-project
```

WSL里运行的Codex用WSL的用户目录；Windows原生运行用该Windows用户对应目录。没有命令修改`config.toml`或切换网络模式。安装后用`$jjf-external-deck`调用；未显示时重开会话。公开分发插件是另一项工作，此ZIP没有自动发布到插件市场。

独立安装用户指定`image-to-editable-ppt`见`references/editable-ppt-integration.md`；本包不会静默安装远程代码。未来运行需实际图片能力；多页转换按上游要求需page workers；Canva导入需相应连接授权。

## 直接交给Codex的启动语

```text
使用 $jjf-external-deck。先读SKILL.md、品牌规范和会话复盘。
我需要JJF对外宣传Deck，面向[政府园区/企业集团/开发者/教育]。
主题是[主题]，基于我提供的材料，不虚构人数、案例与合作角色。
先形成内容锁和逐页视觉节奏；确认3张代表页后再扩展。
沿用正式Logo和黑绿体系，逐页变化构图，避免办公室/绿环/卡片重复。
图片定稿后实际调用 $image-to-editable-ppt，验收可编辑文字和独立素材。
最终交付逐页PNG、可编辑PPTX及QA报告。[需要时：另导入新的Canva设计。]
```

## 项目辅助命令

```bash
python scripts/deckctl.py init --project ./jjf-opc
python scripts/deckctl.py validate --project ./jjf-opc
# 先编辑content-lock.json：每页填写精确visible_text，visible_text_status设为locked；取得真实内容审批后：
python scripts/deckctl.py lock-content --project ./jjf-opc --evidence "本项目实际的内容审批记录"
python scripts/deckctl.py register-preview --project ./jjf-opc --page 6 --image /absolute/path/to/actual-output.png
python scripts/deckctl.py approve-preview --project ./jjf-opc --page 6 --reviewer user --evidence "用户明确选择本页当前版本的原话/记录" --visual-reviewed
python scripts/deckctl.py handoff --project ./jjf-opc --pages 6
```

图片登记/批准需Pillow（`python -m pip install Pillow`；在用户允许的隔离环境）。其余管理脚本使用Python标准库。handoff只产交接包，输出`conversion_executed=false`；执行者仍须真正调用上游Skill。严禁用假审批文字运行approve。

完整内容锁需审批时：编辑`content-lock.json`后执行`lock-content`并填写真实依据。该动作使受影响页的旧图片审批失效。脚本只验证哈希与字段，不能替人判断内容真实或图片美观。

v1.0.2起，重新锁定只使内容发生变化的页失效；其他页的候选/批准稿保留。旧项目缺少按页哈希时，首次重新锁定保守失效，之后按页追踪。已有自动纠错授权可以作为真实依据，由delegated-design-lead验收，不伪造用户逐页批准。init和handoff同时携带原PNG与官方主SVG及其哈希；SVG不支持时仍可使用PNG。

## 文件导航

- `references/session-retrospective.md`：完整会话流程、成功点与失败点。
- `references/brand-and-visual-system.md`：设计语言、Logo、字体、色彩与节奏。
- `references/opc-storyboard.md`：OPC19页工作基线。
- `references/narrative-and-evidence.md`：受众、叙事与事实边界。
- `references/workflow.md`：制作/改稿/审批/交付顺序。
- `references/editable-ppt-integration.md`：指定转换器的真实状态机与命令。
- `references/canva-handoff.md`：新设计导入与二次验收。
- `references/canva-in-place-editing.md`：已有Canva局部修改、品牌组件统一与非目标内容保护。
- `assets/logo/README.md`：三种官方SVG的用途、来源与字标编辑边界。
- `references/qa-and-release.md`：视觉、内容、编辑性验收。
- `assets/`：官方Logo、设计tokens、带状态标签的参考缩略图。
- `templates/`、`prompts/`：可复制项目文件与执行模板。
- `scripts/`：版本与输入守卫、PPTX结构初筛、本地安装。
- `tests/`：脚本测试及待执行的行为评测。

## 不包含

不附字体；不附内部投标报价与联系人明细；不附第三方密钥；不附上游转换器源代码；不把过去的失败稿当正式Deck。

## 补充PPTX结构检查

```bash
python scripts/audit_pptx.py /path/to/edited.pptx --handoff /path/to/page_map.json --out /path/to/qa/structure.json
```

这个脚本故意不会把release_ready设为true：视觉保真、真实编辑试验、Canva验收不能由XML检查替代。测试运行使用Python 3、Pillow、python-pptx；核心审计本身只需标准库。
