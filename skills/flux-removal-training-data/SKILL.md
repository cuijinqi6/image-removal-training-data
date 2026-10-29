---
name: flux-removal-training-data
description: 使用 FLUX Precise Editing 制作汽车、人物/人群、物品及关联阴影/倒影消除训练数据；支持已有标注或经审核的语义实体mask、尺寸校准、局部回贴、质检、断联续跑和审核后目录式发布。
---

# FLUX 消除训练数据

训练关系：`工作原图 + 实体mask → 对象及关联阴影/倒影均被移除的target`。实体mask不包含外部投射阴影或倒影；差分辅助区域只决定回贴范围。target在辅助support外逐像素保留工作原图。

## 先确定当前状态

续接已有项目时，先读项目最新摘要、存储约定和状态JSON，再决定行动。已完成并发布的批次不自动重跑；待修项不等于已授权无限重试。不加载全部旧日志、历史浏览器ID或逐次失败记录。

本技能可跨agent使用，不依赖Codex会话。网站为 https://flux-tools.bfl.ai/precise-editing ，模型默认FLUX 3 Large，以当前页面为准。Windows/其他设备默认使用正常可见Chrome；用户明确授权Edge、内置浏览器或双浏览器时遵循该授权。只用当前agent获准的浏览器工具，不调用隐藏接口或绕过验证。

Chrome是浏览器选择，不等于必须用Windows原生鼠标键盘控制。存在已连接的专用浏览器工具时优先发现其标签页并核验URL，再操作。若工具因无法确认当前URL而安全中止，本轮停止浏览器操作，保存状态并交用户手动恢复；不能按普通连接超时重试或换接口绕过。

## 执行顺序

1. **确认范围。** 指定实例还是全部真实人群，是否含附件、骑乘车辆、牵引动物及关联倒影。保留广告人像、雕像、无关停放车辆、设施与环境反射。使用[提示词](references/prompts.md)。
2. **准备工作图与实体mask。** 保留原图，EXIF转正后统一坐标；按[尺寸记录](references/resolution.md)就近resize，mask只用最近邻。无标注时读[无标注人群流程](references/unannotated-crowds.md)，生成候选并审核最终合并mask，不假设已有全景标注。
3. **浏览器生成。** 按[网站与恢复](references/browser-and-recovery.md)上传、填prompt、生成、选择正确版本并保存raw。累计每样本最多3次请求；结果未知不盲目重发。解码与视觉核验前保留结果页。
4. **局部回贴。** 按[数据流程](references/data-workflow.md)分开维护实体mask、辅助编辑mask和保护区域。差分抑制微小色差后仍须审核完整阴影/倒影范围；泛用脚本不会自动识别阴影。raw未清干净时扩大support无效。
5. **逐张审核。** 查看原图/最终mask叠加、三联图、原图/raw/target完整投影范围和所有残留候选放大图。检测为零不保证无人；新露出的广告人物可保留但必须判明身份。身份、覆盖或接缝不确定则待修。
6. **导出与发布。** 读[批处理、发布与交接](references/batch-publishing-handoff.md)。仅accepted进入四目录和公开清单。发布按用户明确授权，保留原仓库数据，核对远端后才报告完成。

## 审核硬条件

- input/mask/target同尺寸；训练文件无损PNG，mask二值0/255且非空；三联图可用JPG。
- 实体mask不把广告、固定人像、倒影误作真实目标，不漏需要移除的明显实例；近似模型边界如实记录。
- 对象、指定附件及关联阴影/倒影完整消失；无明显新增人物、误删设施、结构错位或接缝。
- support外像素差为零。“原图”指resize后的工作图，不是未经缩放的源文件。
- input/mask审核绑定当前两者哈希；残留、阴影/倒影审核绑定当前target哈希。文件变化后旧审核失效。
- 文件齐全、请求成功、检测为零、support外差为零，任何一项单独成立都不能自动标accepted。

## 自带脚本与能力边界

Python 3.10+，依赖见requirements.txt。数据路径由调用者提供，遵守项目指定的数据盘。

- `scripts/prepare_sample.py`：已有二值/实例ID标注的EXIF坐标检查与resize。自动尺寸仅覆盖首轮4:3/3:4表；其他尺寸校准后显式传--size。
- `scripts/local_paste.py`：用已审核对象/阴影或编辑mask合成target，输出core/support/alpha和不变性报告；颜色匹配默认关闭。
- `scripts/export_sample.py`：单样本校验；--reviewed表示调用者已完成视觉审核，不会自动审核。
- `scripts/audit_resume.py`：只读盘点状态；可核验accepted文件、哈希、审核绑定及support外不变性，不提交请求、不修改状态。
- `tests/test_pipeline.py`：不含私人图片的合成验证。

包内不含语义分割模型、网站控制器、自动阴影识别或GitHub凭据。项目专用脚本必须先读说明/副作用再复用，不能把旧批次一次性修补脚本直接套到新批次。
