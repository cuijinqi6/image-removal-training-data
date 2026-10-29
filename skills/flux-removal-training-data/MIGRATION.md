# 迁移与调用

保留整个flux-removal-training-data目录。Codex可放入~/.codex/skills；其他支持SKILL.md的agent放其技能目录；没有自动发现能力时直接读取SKILL.md并按需读取references。agents/openai.yaml可被其他agent忽略。skill不绑定模型，新会话自行选择模型与推理级别。

Windows/非Codex设备默认正常Chrome；用户明确授权Edge等时按其指示。先发现当前agent的浏览器、上传和下载能力，登录和验证在目标设备正常完成。不复制原设备cookies/令牌，不绕过验证。没有浏览器工具时由用户手工上传/生成/下载，本地Python流程可继续。

新项目先确认目标和存储盘，安装requirements.txt后运行tests/test_pipeline.py。已有项目先读其最新摘要与权威状态，不重跑已经发布数据。skill只包含通用流程与合成测试，不包含私人照片、模型权重、浏览器控制器、凭据或当前项目路径。

调用示例：
“使用$flux-removal-training-data，先读本项目最新摘要与AGENTS.md，盘点状态。从这批原图制作实体mask和连带阴影/倒影移除的target；先做少量完整样本。所有新文件放项目指定盘，只发布审核通过数据。”

原图无实例标注时，先读references/unannotated-crowds.md；泛用prepare_sample.py需要已生成并审核的二值/实例mask，不自动执行语义分割。阴影/倒影范围必须提供或审核辅助编辑区域，不能仅凭差分自动断言归属。

尺寸表属于历史实测，跨设备先用下载文件解码校准。恢复、请求状态、目录式发布与交接分别见references/browser-and-recovery.md、batch-publishing-handoff.md。Code 10只表示可见验证失败，不能单凭它认定限流/IP封禁。

便携包只用于分发skill，与用户目录式训练数据分开；不把skill ZIP上传训练数据仓库。
