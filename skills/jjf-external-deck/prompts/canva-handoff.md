# Canva执行交接

先判断任务：以下是新Deck导入路线。用户明确要求修改已有Canva时，读取 `references/canva-in-place-editing.md`，沿用授权，只操作指定页/对象，提交后回读原设计；不得为改Logo或错字重新导入整套。

把已通过编辑验收的【PPTX文件】导入为一个新的Canva presentation，保留旧官方介绍。
先读取当前Canva工具schema，使用支持的design_file或正式上传流程；不得为生成公共URL上图床。
先用3页代表稿验证字体、Logo、图层、页序与可编辑性，再处理全稿。真正修改标题、移动一个图形、替换一张图片进行试验；必要时在测试副本进行。
保存design_id、编辑链接、导入状态、检验结果及字体/效果差异。上传了一个整页PNG不算完成此任务。

按项目 typography-contract.json 和 `references/typography-consistency.md` 横向核对同角色标签。读回真实文字属性与位置生成 inventory；当前工具若不能读/设字体家族，不以字号/字重修改冒称字体统一。普通页码/网址保留原生文字，不静默转 SVG 轮廓。保存后逐页截图复查，报告已验证字段和 unknown。
