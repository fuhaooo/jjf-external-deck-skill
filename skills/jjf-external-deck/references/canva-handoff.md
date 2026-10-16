# Canva 交付

## 推荐链路

批准图→指定image-to-editable-ppt→对象级PPTX验收→导入新的Canva设计→Canva内再验收。或者原生PPT直接导入。把整页PNG放入Canva只会得到图片，不应称为已完成可编辑拆解。

已有可编辑Canva且用户明确要求原地修改时，不走本节的新建导入链路；读取 `canva-in-place-editing.md`，在指定原设计中局部修订并保存。

本次仅核查了连接器能力和官方文档，没有新建Canva设计、修改原稿或实际验证这套19页的导入。

## 当前连接器合同（2026-10-16核查；执行时重读）

已发现`Canva.import-design-from-url`：可将本对话文件通过`design_file`导入为新设计，`intended_design_type="presentation"`；文件字段使用运行时支持的文件引用/本地自动转换路径，不能编造ID。已有公开HTTPS来源可用`url`，二者不可同时给；私有文件不能为了URL而上图床。

仅在确有需要时使用`Canva.create-upload-url`，按照当前返回的格式、method、headers和文件类型限制上传；不能假定图片资产上传地址也接收PPTX，不能重用失效/已用地址。优先使用导入工具实际支持的design_file。`upload-asset-from-url`只是资产上传，不等于创建多页可编辑设计。单张图的重建工具即使存在，也不自动替代用户指定的转换步骤。

是否能在特定宿主传绝对路径取决于实际文件参数映射。导入失败先读错误和schema，尝试正确文件引用；不能公开托管绕过、不能宣布完成。用户只问方法时不调用写操作。

## 原稿保护

旧官方介绍保留，只读取品牌与业务资料。默认import会创建新design，记录design_id、edit URL与版本。只有用户明确说更新某个原设计，才使用兼容的更新动作；不以新副本假装原稿已更新。

## 兼容性与验收

Canva官方帮助列出PowerPoint导入及字体匹配局限；图表、SmartArt、WordArt和真正3D对象可能不被支持。复杂视觉优先保留可替换的图片，结构图使用简单原生元素；必要时分别交付“PowerPoint语义完整版”和“Canva兼容版”，不可把后者说成同等可编辑。

第一轮先导入3张代表页：文字密集页、复杂主视觉页、图表/流程页。核对页数与順序、标题换行、中文字体、Logo、透明度、图层、箭头、裁切、备注与网站。试改标题、移动图标、替换图片，再导出PNG/PPTX对照。全套通过后记录`canva_verified`。仅有design_id表示创建成功，不等于验收通过。

不要在Skill写死文件体积、页数、元素上限，执行时查官方当前限制。超过限制时说明影响并按明确页序分卷，不静默漏页。

## 参考

- Canva Connect设计导入： https://www.canva.dev/docs/connect/api-reference/design-imports/
- Canva官方PowerPoint帮助（本次可读区域版）： https://www.canva.com/en_in/help/powerpoint-import/
- 本会话实际发现的Canva工具schema。工具优先于旧教程，不通过未知HTTP接口臆造上传。
