# 批处理、发布与交接

## 状态与版本

每样本独立JSON，临时文件写完原子rename。保留id/source_group、源图哈希、尺寸变换、prompt/model、实际提交累计attempt、stage、raw所属attempt、文件路径/哈希、选择/排除实体、保护区、审核与问题。仅预留未点击的次数不算实际请求；旧候选不能冒充最后失败请求的结果。

正常阶段可为prepared → awaiting_upload → uploaded → submitting → generating → downloaded → pending_visual_review → accepted。异常/待修分为needs_review、mask_review_pending、generation_failed、unknown_submission、blocked_browser_verification、no_valid_entity_review。必须区分生成完成、审核通过和文件齐全。

- 点击Generate/Retry前落盘submitting，观察在途后记generating。失败也计实际请求；同源图累计最多3次，不清零。
- 未知请求保留unknown_submission，不自动当失败重发。
- 版本选择状态绑定样本、attempt、当前tab；新任务/重试重置，不能沿用上一个V1标记。
- raw保存后解码、检查尺寸及内容，本地审核结束前不关闭结果页。
- 第三次失败但有旧候选时保留needs_review及最后请求失败信息，不自动通过旧图。

只读盘点：
```text
python scripts/audit_resume.py --state-dir STATE_DIR --output-dir DATASET_DIR --verify-files --report AUDIT_JSON
```
该工具适用于本技能约定的扁平四目录与同名JSON，不更新视觉结论、不读浏览器。项目的review()/select()等可能重置stage或重建mask并丢失分块补充，调用前先看实现。

## 导出

input/、mask/、target/为PNG，comparison/为三联JPG；同名一组。raw、原坐标mask、core/support/alpha和重试候选留在work，不混入accepted。保存全量源图状态表，另导出仅accepted目录。

accepted须有与当前文件一致的三类审核：
1. source-mask绑定input与mask SHA-256。
2. 残留绑定target SHA-256；所有候选逐一判读，包括mask外新生人形。
3. 阴影/倒影绑定target SHA-256；看过原图、实际使用raw与target完整投影范围。

另核验同尺寸、二值非空mask、support外像素一致。改mask/target后重新合成和审核。近似边界和合成监督属性如实记录。同源图、近似场景与重试版本不跨训练/验证分组。

## 目录式GitHub合并

用户明确授权公开发布后执行。既有仓库先看本地/远端，不覆盖他人更新、不重建仓库。仅追加accepted的新ID；冲突比较SHA-256，不静默覆盖。保留原图片及元数据，清单去重并更新数量。

公开manifest字段白名单：ID/分组、尺寸、模型/prompt、实体选择、mask来源、必要审核、相对路径、大小与SHA-256。去掉本机绝对路径、浏览器ID、cookies、令牌和带鉴权参数的来源链接。目录式交付不上传ZIP；技能便携ZIP与数据分开。

提交前核验四目录计数、图片哈希、旧图片未改、无ZIP和敏感字段。push后核对远端提交、公开性、完整Git树blob和旧样本；远端一致才报告上传完成。大推送暂时无输出时保留进程，不重复push。

## 精简交接

项目维护一份最新摘要：目标、完成状态、有效授权/约束、活动数据盘、权威状态/审核文件、专用脚本及副作用、未解决项、下一步。私人路径不放进通用skill。

新会话先读摘要和相关参考，再只读盘点。已发布批次不自动重跑，等用户指定新批次或待修子集。不恢复失效浏览器ID、旧控制器、轮询日志和废弃方案。保留原始证据，活动摘要只保留有效结论。模型/推理级别由新会话设置，skill与摘要不绑定模型。
