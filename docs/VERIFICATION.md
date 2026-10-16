# 验证说明

当前发行版本见 [VERSION](../VERSION)，版本对应的机器记录见 [verification-report.json](verification-report.json)。

验证日期：2026-10-16。环境：Python 3.12.7、Pillow 12.3.0、python-pptx 1.0.2。测试复用了任务环境已有的隔离依赖，未修改全局Python安装。

## 已执行

- 43项核心测试通过：保留既有25项脚本/品牌测试，新增18项语义角色文字审计测试。新增项覆盖字体漂移、缺测、CJK覆盖、颜色、尺寸/坐标归一化、原生文字和目标页覆盖。
- 20项离线发布/版本一致性测试通过；新增9项覆盖版本缺失/漂移、概览旧标题、使用范围、报告版本和同步边界。
- skill-creator格式检查通过。其验证器在Windows默认GBK编码下读取中文失败，设置进程级PYTHONUTF8=1后通过；没有修改系统验证器。
- 临时项目安装成功，三种SVG字节完整，重复安装拒绝覆盖。
- 本次目录整理后重新在临时项目安装，确认随包VERSION及NOTICE与仓库一致，随包README链接可解析，重复安装仍拒绝覆盖。
- 三种SVG已在本地浏览器实际渲染并检查；来源哈希与原官方文件一致。原PNG保持不变。
- 独立Agent完成一次只读局部Canva修订场景推演；未调用外部服务或实际编辑Canva，见SKILL-REVIEW.md。
- v1.0.3新增只读文字一致性场景评审；确认平台缺少字体属性时必须报告未完成，不能以字号一致冒充字体家族一致。审计CLI缺测返回unknown/退出码2。
- 仓库与Skill两级哈希清单、相对文件链接、文件类型及凭据模式检查作为发布前门禁执行。

命令：

```bash
python -m unittest discover -s skills/jjf-external-deck/tests -v
python -m unittest discover -s tests -v
python scripts/check_release.py
```

## 远程发布证据

本地测试不证明GitHub上传成功。实际推送后，需回读远端分支、commit、README和SVG blob，与本地一致才报告成功；对应结果单独记录到被Git忽略的.publication.json。本轮指定目标为fuhaooo/jjf-external-deck-skill，不能因为它已存在而另建仓库或覆盖远程历史。

## 未作为本版本端到端验证完成

真实复杂页生成、OCR、指定转换器重建、完整19页可编辑转换、Canva导入保真及所有Agent兼容性均未由本次本地检查验证。v1.0.2的SVG渲染记录保留，本轮目录整理未重复图像渲染。原18项模型行为场景保留未运行，不因局部独立只读推演或目录检查而标为通过。

文件哈希、单元测试和凭据模式扫描不是完整安全审计或像素级视觉保证；本仓库是Skill，不是已完成的Deck。
