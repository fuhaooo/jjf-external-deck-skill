# 给 image-to-editable-ppt 的 JJF 交接

实际调用 `$image-to-editable-ppt`，将本次handoff列出的【已批准图片】转为可编辑PPTX；不得重新策划叙事或套其他主题。

按page_map排序并保留JJF源页号。读取安装版SKILL.md、cli-helper、manifest-schema与page-decision-tree；安装与backend情况先检查，缺失报告明确阻塞。

正式Logo来源：【logo路径/hash】；将Logo作为独立图片，不OCR、不生成替代品。
文字校对依据：【content-lock与逐页精确visible_text】；源图与文字锁有冲突时先停该页处理，不静默选择其一。

标题、正文、数据、简单框线、流程箭头原生可编辑；照片、3D材质等保留独立可替换视觉，清理底图文字。不把整页原图放底下再覆盖文字。不改品牌、不擅删内容、不把示例变事实。

敏感级别：【classification】；外部处理授权：【scope】；预算与并行：【caps】。尊重本机/运行时更高优先级权限与OCR规则；不得把上游的额度宣传当保证。

先代表页试运行，合格后批量。多页使用真实workers，单页按--local状态登记；不伪造dispatch/accepted。最终返回真实PPTX路径、上游validation、每页素材编辑边界、未解决差异。

JJF补充验收：内容锁/品牌/跨页节奏/改字移动替图测试。Canva是独立后续动作，未经用户要求不要导入或覆盖原设计。
