# 消除提示词

用位置、颜色/服装明确目标，不能只写“specified”。单实例只删指定实例；只有用户要求整幅真实人群清空时使用全人群模板。prompt不替代结果审核。

## 简短模板

汽车：
> Remove only [vehicle description] and its cast/contact shadows. Reconstruct the background naturally. Keep everything else unchanged.

人物/指定人群：
> Remove only [person/group description] and their cast/contact shadows. Reconstruct the background naturally. Keep everything else unchanged.

物品：
> Remove only [object description] and its cast/contact shadows. Reconstruct the background naturally. Keep everything else unchanged.

用户要求关联倒影时，在shadows后加入 `and complete reflections on the ground, water and glass`。保留无关对象的阴影和环境反射。

## 全真实人群（含阴影与倒影）

> Remove all real people, including tiny, distant and partly hidden people and visible shop staff, their carried items, ridden bikes/scooters and led dogs, with all associated shadows and complete reflections. Reconstruct an empty scene with no new people. Preserve advertising images, statues, parked vehicles, furniture, signs, lighting and environmental reflections. Keep everything else unchanged.

骑乘车辆、狗、附件按用户范围选择。无人停放车辆不自动当关联目标。

## 定向重试

保留全局范围，只补充实际看到的残留位置，例如：
> Also remove the pale-shirt vendor behind the lit food stall on the right, including their full pavement reflection. Preserve the stall and goods.

区分raw本身残留与回贴重新带回残留。后者先修辅助support，不重复请求。无法确定真人/广告/雕像身份时暂停该样本，不用更强prompt代替身份判断。
