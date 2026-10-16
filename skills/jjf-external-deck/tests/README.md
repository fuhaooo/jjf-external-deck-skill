# 验证方法

`python -m unittest discover -s tests -v`从Skill根目录运行25项本地测试。依赖Pillow与python-pptx；生产版结构审计只需Python标准库。v1.0.1的19项保持通过，v1.0.2新增6项按页审批和官方SVG资产回归测试。

两组测试先在实现前运行，分别观察13项/6项失败，再完成实现并重新执行。fixture中的审批字句只在TemporaryDirectory中使用，不是实际用户审批。

覆盖：页序/主题保留、内容哈希变化、非覆盖式初始化、图片实际存在与revision、审批证据、视觉检查声明、旧批准稿保护、源图被篡改、图片顺序映射、PNG伪编辑、原图加文本覆盖、原生文本与锁比对、损坏PPTX以及不附字体。

不覆盖：模型在新会话是否实际遵循Skill、图像审美、真实复杂页拆解、第三方OCR/图片API、Canva导入保真。behavioral-evals.json提供18个待执行行为场景，结果保持null，不写成通过。

验证上游集成：未来必须在用户运行环境中做代表页真实转换并保存CLI/version、run、manifest、validation、preview/diff及编辑实验；否则一直标documented_not_live_tested。
