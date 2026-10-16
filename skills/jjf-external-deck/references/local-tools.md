# 本地项目命令

这些命令用于管理内容锁、预览版本和转换交接；不会生成图片或执行外部转换。命令从 Skill 根目录执行，`scripts/` 与本文件的上级 `references/` 同级。

将示例中的 `/absolute/path/to/deck-project` 换成用户选定的实际工作目录；图片路径也必须替换成真实文件。项目应位于 Skill/仓库目录之外，不把客户材料或生成稿放进安装包。

## 初始化和校验

```bash
python scripts/deckctl.py init --project /absolute/path/to/deck-project
python scripts/deckctl.py validate --project /absolute/path/to/deck-project
python scripts/deckctl.py --help
```

`init` 以 OPC19 作为引导模板。其他受众先按[叙事预设](narrative-presets.md)替换内容锁页纲，再锁定内容，不直接套用 19 页。项目会携带官方主 SVG 和 PNG 兼容版及其哈希。

## 内容锁、图片和交接

先编辑项目 `content-lock.json`：逐页填写精确 `visible_text`，将 `visible_text_status` 设为 `locked`；使用实际审批依据，不复制示例文字伪造授权。

```bash
python scripts/deckctl.py lock-content --project /absolute/path/to/deck-project --evidence "本项目实际的内容审批记录"
python scripts/deckctl.py register-preview --project /absolute/path/to/deck-project --page 6 --image /absolute/path/to/actual-output.png
python scripts/deckctl.py approve-preview --project /absolute/path/to/deck-project --page 6 --reviewer user --evidence "用户明确选择本页当前版本的实际记录" --visual-reviewed
python scripts/deckctl.py handoff --project /absolute/path/to/deck-project --pages 6
```

用户已授权自行纠错/设计验收时，可使用 `--reviewer delegated-design-lead` 并填写真实授权和验收依据，不冒称用户逐页批准。仅登记实际检查合格的当前图片。

重新锁定时，仅变化页的候选和批准稿失效，其他页保留；缺少按页哈希的旧项目首次迁移保守处理。脚本验证哈希与状态，内容真实性和视觉质量仍需实际审核。

`handoff` 只产交接包，明确输出 `conversion_executed=false`。执行者继续按[转换集成规范](editable-ppt-integration.md)调用已审阅的独立转换器；不能把交接 JSON 当作转换完成。

## 可编辑交付检查

```bash
python scripts/audit_pptx.py /absolute/path/to/edited.pptx --handoff /absolute/path/to/page_map.json --out /absolute/path/to/structure.json
python scripts/audit_typography.py /absolute/path/to/typography-contract.json /absolute/path/to/typography-inventory.json --out /absolute/path/to/typography-audit.json
```

PPTX 检查只做结构和文字初筛，`release_ready` 不会自动设为 true。文字审计读取真实提取的属性，不自动连接 Canva 或解析 PPTX 的继承字体；缺测返回 unknown。具体字段及退出码见[标签一致性规范](typography-consistency.md)。

图片登记/批准使用 Pillow；两个审计脚本只需 Python 标准库。开发测试另需 python-pptx。依赖须放在用户允许的隔离环境，不自动修改全局 Python。

## 本包测试

```bash
python -m unittest discover -s tests -v
```

这里的 `tests/` 是本 Skill 随包测试；仓库级发布检查在仓库根目录执行，见[维护者指南](https://github.com/fuhaooo/jjf-external-deck-skill/blob/main/docs/PUBLISHING.md)。脚本测试不能代替实际生图、转换、截图对照和编辑实验。
