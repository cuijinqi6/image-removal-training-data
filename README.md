# Image Removal Training Data

用于人物 / 人群及其关联阴影、倒影消除的合成训练数据。当前收录 **78 组已审核通过的样本**，来自 crowd batch 3。图片直接存放在仓库目录中，无需解压。

## 目录

| 目录 | 数量 | 内容 |
| --- | ---: | --- |
| `input/` | 78 | 消除前工作图，无损 PNG |
| `mask/` | 78 | 二值实体 mask，无损 PNG；0 为保留，255 为待消除实体 |
| `target/` | 78 | FLUX 候选经局部回贴后的目标图，无损 PNG |
| `comparison/` | 78 | 原图、实体 mask、目标图三联对比 JPG |

同名文件构成一组样本，例如 `input/101.png`、`mask/101.png`、`target/101.png`、`comparison/101.jpg`。各样本的三张训练图尺寸一致；不同样本的工作尺寸可能不同。工作图已根据生成尺寸 resize，并非未经缩放的源文件。

## 训练语义

- 输入为原图和指定实体 mask。mask 仅表示选定实体本体，不包含其外部投射阴影或镜面倒影；部分样本同时选择被骑乘车辆或被牵引动物。
- 目标图同时移除对应实体及其阴影 / 倒影，因此目标变化可以出现在训练 mask 外。
- 差分辅助区域只用于确定局部回贴范围，未作为训练实体 mask。
- 保存后已核验：回贴 support 外的目标像素与工作原图逐像素一致；该检查不代表全部 mask 外像素都不变。
- 这些目标图属于经审核的 FLUX 合成监督，不是实拍的无目标背景真值。

本仓库只包含审核通过的 78 组；待审 / 待修样本与生成失败项未纳入。

## 清单与校验

- [`samples.csv`](samples.csv)：样本路径与尺寸。
- [`manifest.json`](manifest.json)：生成提示词、mask 来源、审核记录、文件 SHA-256。
- [`sample_ids.txt`](sample_ids.txt)：当前样本 ID。
- [`SHA256SUMS.txt`](SHA256SUMS.txt)：全部 312 个图片文件的校验值。

Linux / macOS 可在仓库根目录执行 `sha256sum -c SHA256SUMS.txt`。三联图保存在 `comparison/`，可用于人工复核。

更新日期：2026-10-25。
