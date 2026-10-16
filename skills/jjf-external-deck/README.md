<p><img src="assets/logo/jjf-logo-master.png" alt="JJF official logo" width="72" /></p>

# JJF External Deck

[安装包版本](VERSION) · [Agent 入口](SKILL.md) · [项目命令](references/local-tools.md) · [品牌资产](assets/logo/README.md) · [使用范围](NOTICE.md)

这是可独立安装的 JJF AI Craft Labs Skill 包，用于品牌介绍、OPC 生态方案、企业 FDE、AI 培训、开发者社区与海外活动 Deck。安装包与仓库使用同一发行版本。

## 从这里开始

- 使用者：安装后以 `$jjf-external-deck` 调用；完整安装方式见[仓库安装说明](https://github.com/fuhaooo/jjf-external-deck-skill#安装)。
- Agent：读取 [SKILL.md](SKILL.md)，再按任务加载相关参考文档。
- 手动管理项目：查看[本地项目命令](references/local-tools.md)，将 Deck 项目放在 Skill 目录之外。
- 检查版本：读取本目录的 [VERSION](VERSION)。它随安装包复制，由仓库根 `VERSION` 同步生成。

## 包含的工作流程

1. 依据真实资料确定受众、叙事、页序与精确文案。
2. 使用官方 SVG Logo 和黑绿品牌系统，逐页选择构图和视觉重点。
3. 将已批准图片交给独立的 `image-to-editable-ppt` Skill，验收原生文字、简单结构和独立视觉素材。
4. 对页码、章节、网址等重复标签共用文字样式合同，拆解后及 Canva 保存后检查一致性。
5. 修改已有 Canva 时备份并局部编辑，保护其他对象、已有页面及用户改动。

图片生成、OCR、转换器和 Canva 仍需实际运行环境提供相应工具与权限。本包不自动安装远程依赖或开通服务；本地检查不代表完整转换或 Canva 保真验收通过。普通文字保留原生可编辑能力；工具不能设置的字体属性须明确报告。

## 目录导航

| 路径 | 用途 |
|---|---|
| [SKILL.md](SKILL.md) | Agent 的任务入口与行为规则 |
| [VERSION](VERSION) · [NOTICE.md](NOTICE.md) | 随包携带的发行版本和使用范围 |
| [agents/](agents/) | Codex 展示信息和调用策略 |
| [assets/](assets/) | 官方 Logo、品牌 tokens 与有状态说明的参考图 |
| [references/](references/) | 按任务读取的叙事、设计、转换、Canva 和验收规范 |
| [prompts/](prompts/) · [templates/](templates/) | 生成、修订、交接提示词与项目模板 |
| [scripts/](scripts/) | 项目管理、PPTX 检查、文字一致性审计、本地安装 |
| [tests/](tests/) | 脚本回归测试及待执行的模型行为场景 |
| [MANIFEST.sha256](MANIFEST.sha256) | 相对本目录的文件校验清单 |

常用规范：[工作流](references/workflow.md) · [转换集成](references/editable-ppt-integration.md) · [标签一致性](references/typography-consistency.md) · [现有 Canva 修订](references/canva-in-place-editing.md) · [交付验收](references/qa-and-release.md)。

## 从本地包安装

以下命令从本目录执行，需要 Python 3.10+：

```bash
python scripts/install_local.py --scope user
# 仅安装到选定项目时：
python scripts/install_local.py --scope project --project /absolute/path/to/jjf-project
```

安装器复制完整目录到目标 `.agents/skills/jjf-external-deck`，拒绝覆盖同名安装，不下载依赖、不修改用户设置。WSL 与原生 Windows 应在各自实际运行环境中安装。更新前先备份并比较旧版本。
