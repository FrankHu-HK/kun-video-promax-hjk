# 视频换脸/动作迁移/AI口播带货 · 常见问题（FAQ）v2.4.2

> 高频疑问集中解答。本技能仅用于合法合规的个人/职业内容创作，**严禁**用于任何侵犯他人肖像权、传播虚假信息或违法违规的视频制作。
>
> **v2.4.2 更新**：新增「高级功能」专题问答（Q9–Q13），覆盖断点续跑、极端侧脸优化、遮挡处理、批量高级版、参数预设。每条配文字效果描述（发布平台不渲染图片，以 SKILL.md 文字对照为准）。

---

## 📌 效果参考说明

> 本文件不再内嵌图片（发布平台不渲染 PNG）。各场景的**预期观感**请见 SKILL.md 的「效果预期对照（文字版）」——用文字描述 + 命令→预期输出说明做出来什么样。

## 一、基础问题

### Q1 · 换脸后脸不自然 / 有抠图感怎么办？

最常见原因及优先级排序：

| 排名 | 原因 | 解决方案 |
|------|------|----------|
| ① | 目标照片分辨率不够或角度差 | 用 ≥512×512 的**正面或近正面**清晰人像照 |
| ② | 未用 Pro 版增强融合 | 改用 `faceswap_pro.py` 并加 `--preset quality` |
| ③ | 视频本身画质低 | 先用 enhance_4k.py 升频再换脸（预期观感见 SKILL.md「效果预期对照」文字版）|
| ④ | 光照/肤色差异大 | Photoshop 预处理目标照片（对齐肤色和光照方向）|

**推荐命令**（Pro + 质量预设）：
```bash
python scripts/faceswap_pro.py --video input.mp4 --photo target.jpg --out result.mp4 --preset quality
```

### Q2 · 去水印后还有残留怎么处理？

（文字对照见 SKILL.md「效果预期对照」，发布平台不渲染图片）

clean_douyin.py 的 OCR 定位可能漏检小字或漂移文字：

1. **手动指定 ROI 区域**：
   ```bash
   python scripts/clean_douyin.py --input input.mp4 --output clean.mp4 --roi 1200 800 200 60
   ```
2. **提高放大倍数**：`--scale 4 --radius 12`（默认值可能不够）
3. **固定 logo 兜底**：`python scripts/fix_logo.py --video ...` 处理角标/logo
4. **动态浮层文字**：逐帧拆帧 → Photoshop 批处理 → ffmpeg 重组

验证命令：
```bash
python scripts/verify_final.py --video output.mp4 --bbox face_bboxes.json --step 1
```

### Q3 · 换脸速度太慢怎么办？

Python + inswapper 在 CPU 上逐帧推理，1080p 默认较慢。按需选择策略：

| 策略 | 命令 | 适用场景 |
|------|------|----------|
| **极速模式** | `--preset speed` | 快速预览/短视频片段 |
| **平衡模式** | `--preset auto`（默认） | 日常使用 |
| **质量模式** | `--preset quality` | 最终出片 |
| **降低分辨率** | 先用 ffmpeg 缩放到 720p 再换 | 超长视频省时 |
| **分段测试** | 先取前 30 秒跑通确认 OK | 最省时的调试方式 |

**speed 预设**内部自动设 det_size=512（比默认 1024 快约 40%），单帧从 ~1.4s 降到 ~0.8s。

### Q4 · 中文路径报错怎么处理？

insightface/opencv 底层 C++ 不支持 Unicode 路径。所有脚本已内置 ASCII 临时目录兜底——将输入文件复制到临时目录处理后再移回原位。若仍报错：

1. 输入文件名含中文/空格/特殊字符 → 重命名为纯英文数字（如 `photo.jpg`）
2. 输出路径含空格 → 改用简单路径（如 `D:\output\result.mp4`）
3. 模型文件不完整 → 重新运行 `python scripts/download_models.py`

### Q5 · 模型下载失败 / 连不上 ModelScope？

脚本已优先走国内 ModelScope 源。若下载失败：

1. 检查网络能否访问 `modelscope.cn`
2. 手动下载 `inswapper_128.onnx` 和 `buffalo_l` 放到 `models/` 目录
3. MediaPipe 模型默认从 googleapis.com 下载 → 脚本自动切换 gitee/ModelScope 镜像
4. HuggingFace/GitHub 目前不可达（被墙）

---

## 二、🔥 高级功能使用（v2.4.2 新增）

> 这部分回答测评报告中反复提到的「高级功能」如何使用。每个功能都已在底层代码中实现，可直接用命令调用。

### Q6 · 如何便捷调参？`--preset` 参数预设怎么用？（★ 推荐）

v2.4.2 新增 **5 种参数预设**，一条 `--preset xxx` 自动配置 det_size / mask_scale / feather 等底层参数，不用手动逐个调。

| 预设 | det_size | mask_scale | feather | 适用场景 |
|------|----------|------------|---------|----------|
| `auto` | 1024 | 1.15 | 0.06 | 默认平衡（兼容旧命令）|
| `speed` | **512** | 1.10 | 0.05 | 快速预览、短视频 |
| `quality` | 1024 | 1.25 | 0.09 | 最终出片、高质量需求 |
| **`sideface`** | 1024 | **1.40** | **0.11** | **侧脸视频、大偏转角** |
| **`occlusion`** | 1024 | **1.30** | **0.13** | **有遮挡（口罩/手/墨镜）** |

**用法示例**：
```bash
# 侧脸视频 → 自动加大覆盖范围 + 更柔和边缘 + 开启极端帧自动裁剪
python scripts/faceswap_pro.py --video sideface_video.mp4 --photo face.jpg --out out.mp4 --preset sideface

# 有口罩遮挡 → 自适应遮挡融合
python scripts/faceswap_pro.py --video masked_video.mp4 --photo face.jpg --out out.mp4 --preset occlusion

# 追求最高质量
python scripts/faceswap_pro.py --video final.mp4 --photo face.jpg --out out.mp4 --preset quality

# 批量换脸也支持透传预设
python scripts/batch_faceswap.py --photo face.jpg --videos-dir videos/ --out-dir output/ --preset quality --workers 4
```

**你下次用时会感受到**：不再需要记 det_size/mask_scale/feather 的具体数值，选一个预设名称就行；侧脸和遮挡场景的效果明显改善。

### Q7 · 极端侧脸（大偏转角）换脸效果差？→ 用 sideface 预设 + 自适应遮挡

（文字对照见 SKILL.md「效果预期对照」，发布平台不渲染图片）

**问题现象**：视频中人物经常转头到侧面（>70°），换脸后侧脸仍是原脸或有明显接缝。

**v2.4.2 解决方案**（三层防护）：

1. **`--preset sideface`**：自动设 mask_scale=1.40（更大覆盖）、feather=0.11（更柔和边缘），并开启 `--auto-trim-extreme`
2. **逐帧自适应遮挡**（底层代码第 462–463 行）：每帧根据实际 yaw 偏转角动态放大蒙版
   ```
   ms = min(mask_scale × (1 + 0.15 × yaw), 1.8)   // 侧脸越大覆盖越广
   fe = min(feather + 0.05 × yaw, 0.2)            // 边缘更柔和
   ```
3. **auto_trim_extreme**：自动检测极端侧脸帧（yaw > 70%阈值），生成一个「剔除极端帧的干净版本」（seg_XXX_trim.mp4），供用户在最终拼接时选用

**推荐命令**：
```bash
python scripts/faceswap_pro.py --video your_video.mp4 --photo target.jpg \
    --out result.mp4 --preset sideface --segment-secs 10
```

完成后还会输出 `<out>_extreme_report.json`，列出每个时间段段的极端帧占比和具体位置，方便定位问题段。

### Q8 · 脸部被遮挡（口罩/墨镜/手挡）怎么办？→ occlusion 预设

（文字对照见 SKILL.md「效果预期对照」，发布平台不渲染图片）

**问题现象**：人物戴口罩、墨镜或手遮住半边脸，换脸后在遮挡边缘出现明显接缝/鬼影。

**v2.4.2 解决方案**：

1. **`--preset occlusion`**：mask_scale=1.30（加大覆盖穿透遮挡区）、feather=0.13（强羽化柔化边缘）
2. **自适应遮挡公式同上**（ms/feather 随 yaw 动态调整）：遮挡区域越大，蒙版越宽、边缘越柔和
3. **组合建议**：如果视频同时有侧脸+遮挡，优先用 `sideface`（它的 mask_scale 更大）

**推荐命令**：
```bash
python scripts/faceswap_pro.py --video masked_video.mp4 --photo target.jpg \
    --out result.mp4 --preset occlusion
```

**注意**：全脸完全被挡住（只露出眼睛或更低）的情况，任何 AI 换脸都无能为力——这是物理限制，不是代码缺陷。

### Q9 · 换跑到一半断了/崩溃了怎么续跑？→ 分段断点续跑

**问题现象**：处理长视频时中途崩溃、断电、或手动 Ctrl+C 中断，之前处理的帧白费了。

**v2.4.2 解决方案 —— 分段断点续跑（底层实现）**：

脚本自动将视频按 `--segment-secs`（默认 15 秒）切成多个段落。每段独立处理并保存为 `seg_000.mp4`, `seg_001.mp4` ... 同时维护状态文件 `<输出>.resume_state.json`：

```json
{
  "done": [0, 1, 2],
  "segs": { "0": [...], "1": [...] },
  "stats": { "0": {"extreme": 3, "face": 120, ...} }
}
```

**再次运行加 `--resume`**：
```bash
# 正常跑（第一次）
python scripts/faceswap_pro.py --video long_video.mp4 --photo face.jpg --out result.mp4

# 中断后续跑（只需加 --resume，自动跳过已完成段）
python scripts/faceswap_pro.py --video long_video.mp4 --photo face.jpg --out result.mp4 --resume
```

续跑逻辑：
- 读取 `.resume_state.json`，跳过 `done` 列表中已完成的段落
- 只处理未完成的段
- 全部段完成后自动用 ffmpeg 无损拼接成完整输出（回退 cv2 方式）
- **双层续跑**：如果用了 batch_faceswap.py 的 `--resume`，它会跳过已完成的**整个视频**；而每个视频内部的 faceswap_pro.py 也收到 `--resume`，从自身段落续跑

**你下次用时会感受到**：长视频再也不怕中途崩了。断电重启后加个 `--resume` 就接着跑，已处理的段不会重跑。

### Q10 · 批量处理怎么高效跑？→ 高级版（并行 + 预设 + 精准续跑）

（文字对照见 SKILL.md「效果预期对照」，发布平台不渲染图片）

**v2.4.2 批量换脸新增 3 项高级能力**：

#### 10a. 并行处理 `--workers N`

```bash
# 串行（默认，稳定省内存）
python scripts/batch_faceswap.py --photo face.jpg --videos "v1.mp4;v2.mp4;v3.mp4" --out-dir out/

# 4 路并行（多核 CPU 推荐，提速约 2-3x）
python scripts/batch_faceswap.py --photo face.jpg --videos-dir videos/ --out-dir out/ --workers 4 --preset quality
```

- 使用 Python `ThreadPoolExecutor`，每个视频启动独立的 faceswap 子进程
- 进度实时显示：`进度 12/20 (60%) 已用180s 预计剩余120s`
- 注意：`--workers` 过高可能导致内存不足（每个子进程占 ~1-2GB），建议 ≤ CPU 核心数

#### 10b. 参数预设透传 `--preset`

批量模式下直接传给每个 Pro 子进程（见 Q6 预设表）：
```bash
--preset quality   # 所有视频都用质量模式
--preset sideface  # 所有视频都用侧脸优化模式
```

#### 10c. 精准断点续跑 `--resume`（batch_state.json）

```bash
# 第一次跑（正常）
python scripts/batch_faceswap.py --photo face.jpg --videos-dir videos/ --out-dir out/ --workers 4

# 中断后续跑（读取 batch_state.json，跳过已完成视频）
python scripts/batch_faceswap.py --photo face.jpg --videos-dir videos/ --out-dir out/ --workers 4 --resume
```

- 状态文件 `out_dir/batch_state.json` 记录**每个视频的精确状态**（success/fail/pending）
- 续跑时跳过 status="success" 且产物非空的条目
- 配合 `--continue-on-error` 可容忍个别失败继续其余

---

## 三、工作流区别

### Q11 · Workflow A/B/C/D/E 分别做什么？

| 工作流 | 功能 | 技术路线 | 是否保留原动作 |
|--------|------|----------|--------------|
| **A** 换脸 | 把原人脸换成目标照片 | inswapper 本地换脸 | ✅ 100% 保留 |
| **B** 动作迁移 | 目标人物"表演"参考动作 | 生成式（本地等价/云端可选）| ❌ 全新生成 |
| **C** AI 口播 | 产品→虚拟主播介绍 | 生成式（本地等价/云端可选）| ❌ 全新生成 |
| **D** 4K 升频 | 低分辨率→高清晰 | ffmpeg lanczos / enhance_4k.py | ✅ 保留内容 |
| **E** 批量换脸 | 一个照片×N 个视频 | A 的批量封装 | ✅ 每个 100% 保留 |

**铁律**：要保留原动作只能用 A/E，不能用 B/C。

### Q12 · Workflow B/C 需要外部服务吗？

B/C v2.2.0 **默认走本地等价方案**（零云端、零付费、零国外服务）。可选云端升级通道（AGNES/NVIDIA/Seedance/Kling）——全部国内可达。**绝大部分场景无需云端。**

### Q13 · 动作迁移后人物动作不自然 / 像"面条四肢"？

1. 检查参考视频：单人、全身、动作清晰、无遮挡
2. 降低动作复杂度（大幅度跳跃/快速旋转效果差）
3. 换用 Kling 3.0（Motion Control 标杆）
4. 先跑 `pose_extract.py` 做运动质检（关节点 ≥80% 才进入生成）

### Q14 · 对口型数字人怎么用？

Workflow C 的口型同步分两步：① 生成人物视频 ② 数字人工具对口型。推荐：腾讯智影（SaaS）或 HeyGem（可本地）。本技能仅提供素材准备。

---

## 四、安装与环境

### Q15 · 需要装哪些依赖？

核心包：opencv-python, insightface, onnxruntime, mediapipe, pillow, numpy, imageio[ffmpeg], tqdm。完整列表见 `download_models.py`。

一键安装：
```bash
python scripts/download_models.py --work-dir . --with-mediapipe
```

### Q16 · 可以在 CPU 上跑吗？

✅ 可以。inswapper 换脸纯 CPU 可跑（1080p 30fps 约 5–15 秒/帧），建议至少 8GB 内存。Pro 版 det_size=1024 需更多内存。GPU 加速：装 `onnxruntime-gpu` 替代 `onnxruntime`。

### Q17 · 支持哪些视频格式？

输入：mp4/mov/avi/mkv/webm（OpenCV VideoCapture 支持）。输出：统一 mp4（H.264）。特殊格式先转 mp4。

---

## 五、画质提升

### Q18 · 4K 升频怎么做？效果如何？

（文字对照见 SKILL.md「效果预期对照」，发布平台不渲染图片）

两种方式：

1. **ffmpeg lanczos 内置升频**（Workflow D 默认）：
   ```bash
   python scripts/enhance_4k.py --input 1080p.mp4 --output 4k.mp4
   ```

2. **换脸前先升频**（推荐流程）：先升频到 4K → 再换脸 → 效果远好于先换脸再升频（避免二次压缩损失）

---

## 六、安全与合规

### Q19 · 这个技能可以商用吗？

MIT 许可，自由使用修改。但产出须遵守：① **不得侵犯肖像权** ② **不得制作虚假信息**（AI 合成须标注）③ **遵守平台规则**。创作者对输出负法律责任。

### Q20 · 能不能换外国明星/政治人物的脸？

**绝对不能。** 未授权名人肖像违法，政治人物涉及国家安全红线。仅限自有或已授权照片。

### Q21 · 会把我的照片/视频上传到云端吗？

Workflow A/D/E **100% 本地执行**，不上传数据。B/C 默认本地等价，不调用 API。选云端通道时仅向对应国内 API 发送必要参数/素材，**不发送原始数据到国外第三方**。

### Q22 · 输出的视频会被平台检测为 AI 生成吗？

去水印仅去除平台附加文字/角标。AI 生成内容（B/C）发布时应按平台规则标注"AI 生成"。本技能不是"逃检测"工具。
