# 林澄 Spine 工程

## 当前文件

- `source/lin_cheng.json`：可导入 Spine 4.3 的骨架和动画数据；
- `source/lin_cheng_body.png`：角色上半身；
- `source/lin_cheng_leg_left.png`：左腿；
- `source/lin_cheng_leg_right.png`：右腿；
- `source/lin_cheng_shadow.png`：脚下阴影。

运行时导出位于 `assets/spine/`，使用
`@esotericsoftware/spine-webgl` 4.3.13 加载。

## 动画

- `idle`：1.4 秒循环待机呼吸；
- `walk`：0.6 秒循环行走，左右腿交替摆动，身体轻微起伏。

## 编辑说明

本机安装的是 `Spine Trial 4.3.26`。官方试用许可禁止保存项目、打包纹理和导出
动画数据，因此当前仓库保留的是可导入 Spine 4.3 的开放 JSON 骨架数据，并由官方
WebGL Runtime 直接加载。

取得正式 Spine Editor 许可证后：

1. 打开 `source/lin_cheng.json`；
2. 另存为 `lin_cheng.spine`；
3. 选择 JSON 导出并勾选 `Pack`；
4. 将导出的 JSON、atlas 和 PNG 覆盖到 `assets/spine/`。
