# 标注、回贴和训练数据导出

## Mask职责

训练输入object_mask只包含实例本体，不含外部投射阴影。shadow_mask是归属于该实例的阴影区域；edit_mask是可替代它的审核后对象+阴影联合区域。保护mask可覆盖其他实例与其阴影。

全景标注通常不提供阴影实例关系。已有对象标注不代表阴影标注已解决。可以人工/辅助模型提出阴影候选，但必须审核；原图与生成图差分还包含背景重绘和色差，只能作候选线索。阴影交叠、来源不明的样本优先转人工；无可见阴影提供全黑shadow_mask并记明无阴影，而不是伪造范围。

## 回贴

T=(1-A)I+A F。完整对象+阴影区域及padding内A=1；只在外扩feather环内0<A<1；区域外A=0。脚本直接复制区域外原图并重新读取保存的PNG验证。不得只按对象mask回贴，否则旧阴影仍在。

--color-match默认关闭，可选使用外环RGB差中位数偏移并限制±20，但不保证适用于重绘纹理；应检查局部光照和接缝。输入尺寸不同时报错，不静默调整。尺寸相同仍需检查地平线、地砖、建筑边缘等位置。脚本不自动配准、不自动判断阴影是否消除。

## 输出

每实例一个样本目录：input.png、object_mask.png、target.png；保留flux_raw.png、shadow_mask.png或edit_mask.png、paste_support.png、alpha.png、preview.jpg、report.json及metadata.json。

元数据记录：source_group、目标实例ID与类别、来源文件哈希、工作尺寸、resize记录、模型、prompt、生成尝试、mask来源、审核状态与问题。粗标示范必须pending_review，不能以脚本运行成功标记accepted。

审查：目标本体及附件完整消失；对应投射阴影/接触阴影消失；其他目标及其阴影保留；补全结构和纹理自然；接缝无明显亮度、重影或几何错位。保存后区域外差分应为零，但此指标不能证明生成质量。

按原图或相近场景source_group划分训练/验证/测试，同一原图的实例、尺寸和重试版本不得跨划分。建议先每类30个实例的小试，再比较阴影残留和背景误改；该数量是起步建议，不是硬性要求。模型若硬性只输出对象mask内部，应先修改训练损失与推理合成范围。

依次运行：
```text
python scripts/prepare_sample.py --image IMAGE --annotation PANOPTIC --instance-ids 12 --out-dir SAMPLE_PREP
python scripts/local_paste.py --original SAMPLE_PREP/input.png --flux FLUX.png --object-mask SAMPLE_PREP/object_mask.png --shadow-mask SHADOW.png --out-dir SAMPLE_PASTE
python scripts/export_sample.py --input SAMPLE_PREP/input.png --paste-dir SAMPLE_PASTE --out-dir DATASET/sample_0001 --source-group ORIGINAL_ID
```
审核通过后，最后一条增加--reviewed。正式流程还应在metadata的provenance字段保存prepare记录、prompt、类别、实例ID与生成记录，通过--provenance-json提供JSON。不要将鉴权信息放入该文件。

回贴范围的裁剪检查：人物检测框的顶部不一定覆盖雨伞、帽子或高举物。若按人物框或 gate_top 限制差分范围，须在原图、FLUX原始候选与回贴图上检查整个附件轮廓；原始候选已消除但回贴图留下伞顶等碎片时，修正辅助编辑范围，不能扩大训练实体mask来掩盖问题。补全辅助范围后重新生成target与哈希审查，检查边界亮度和纹理接缝；仍有接缝则保留待修状态。
